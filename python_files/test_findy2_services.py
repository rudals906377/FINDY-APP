import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import auth_gateway.app as gateway
from services.findy2_auth import (
    AuthError,
    authenticate_user,
    create_session,
    delete_user,
    find_usernames_by_phone,
    get_or_create_demo_user,
    read_remote_session_token,
    register_user,
    reset_password_by_phone,
    restore_session,
    social_login_or_register,
    update_user_profile,
)
from services.findy2_media_storage import delete_user_media, store_image
from services.findy2_user_storage import (
    delete_findy2_user_data,
    load_findy2_user_data,
    save_findy2_user_data,
    user_scoped_data_path,
)
from core.findy2_state import create_findy2_state


class Findy2ServiceTests(unittest.TestCase):
    def test_content_detail_state_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            data_path = str(Path(directory) / "findy2-user.json")
            state = create_findy2_state()
            state["answered_question_ids"].add("question-1")
            state["comment_liked_ids"].add("comment-1")
            state["content_reports"].append(
                {
                    "id": "report-1",
                    "contentId": "post-1",
                    "reason": "광고/스팸",
                    "status": "pending",
                }
            )

            self.assertTrue(save_findy2_user_data(data_path, state))
            restored = load_findy2_user_data(data_path, create_findy2_state())

            self.assertEqual(restored["answered_question_ids"], {"question-1"})
            self.assertEqual(restored["comment_liked_ids"], {"comment-1"})
            self.assertEqual(restored["content_reports"][0]["contentId"], "post-1")

    def test_demo_login_account_is_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            auth_path = str(Path(directory) / "users.json")
            first = get_or_create_demo_user(auth_path)
            second = get_or_create_demo_user(auth_path)
            self.assertEqual(first["id"], "user_findy2_demo")
            self.assertEqual(second["id"], first["id"])
            self.assertEqual(second["provider"], "demo")

    def test_phone_verified_signup_find_id_and_password_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            auth_path = str(Path(directory) / "users.json")
            user = register_user(
                auth_path,
                "phone@findy.test",
                "오경민",
                "휴대폰회원",
                "findy1234",
                phone_number="010-1234-5678",
                phone_verified=True,
            )
            self.assertTrue(user["phoneVerified"])
            self.assertEqual(user["phoneNumber"], "010-****-5678")
            self.assertEqual(user["realName"], "오경민")
            self.assertFalse(user["realNameVerified"])

            found = find_usernames_by_phone(auth_path, "01012345678")
            self.assertEqual(found[0]["realName"], "오경민")
            self.assertIn("@findy.test", found[0]["email"])

            reset_password_by_phone(auth_path, "01012345678", "changed1234")
            authenticated = authenticate_user(
                auth_path,
                "010-1234-5678",
                "changed1234",
            )
            self.assertEqual(authenticated["id"], user["id"])

            updated = update_user_profile(
                auth_path,
                user["id"],
                {
                    "name": "새닉네임",
                    "realName": "바꾸려는이름",
                    "username": "changed",
                },
            )
            self.assertEqual(updated["nickname"], "새닉네임")
            self.assertEqual(updated["realName"], "오경민")

            with self.assertRaises(AuthError):
                register_user(
                    auth_path,
                    "duplicate@findy.test",
                    "김파인디",
                    "중복회원",
                    "findy1234",
                    phone_number="010-1234-5678",
                    phone_verified=True,
                )

    def test_gateway_phone_otp_expiry_attempts_and_verification(self):
        gateway.phone_challenges.clear()
        gateway.AUTH_ENV = "development"
        gateway.SMS_PROVIDER = "console"
        client = TestClient(gateway.app)
        original_randbelow = gateway.secrets.randbelow
        try:
            gateway.secrets.randbelow = lambda limit: 123456
            requested = client.post(
                "/v1/phone/otp/request",
                json={"phoneNumber": "010-1234-5678", "purpose": "signup"},
            )
        finally:
            gateway.secrets.randbelow = original_randbelow
        self.assertEqual(requested.status_code, 200)
        request_id = requested.json()["requestId"]

        wrong = client.post(
            "/v1/phone/otp/verify",
            json={"requestId": request_id, "code": "000000"},
        )
        self.assertEqual(wrong.status_code, 400)

        verified = client.post(
            "/v1/phone/otp/verify",
            json={"requestId": request_id, "code": "123456"},
        )
        self.assertEqual(verified.status_code, 200)
        self.assertTrue(verified.json()["verified"])
        self.assertEqual(verified.json()["phoneNumber"], "01012345678")

    def test_account_deletion_removes_auth_data_workspace_and_media(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            auth_path = root / "users.json"
            session_path = root / "session.json"
            base_data_path = root / "user_data.json"
            media_root = root / "media"

            user = register_user(
                str(auth_path),
                "findy@example.com",
                "오경민",
                "FINDY 회원",
                "findy1234",
                phone_number="010-1111-2222",
                phone_verified=True,
            )
            create_session(str(session_path), user)
            data_path = user_scoped_data_path(str(base_data_path), user["id"])
            self.assertTrue(
                save_findy2_user_data(
                    data_path,
                    {"community_posts": [{"id": "post-1"}]},
                )
            )

            image_path = root / "sample.png"
            Image.new("RGB", (32, 32), "#8B6B4F").save(image_path)
            stored = store_image(str(image_path), str(media_root), user["id"])
            self.assertTrue(os.path.exists(stored["path"]))

            with self.assertRaises(AuthError):
                delete_user(str(auth_path), user["id"], "wrong-password")
            self.assertIsNotNone(restore_session(str(auth_path), str(session_path)))

            self.assertTrue(
                delete_user(str(auth_path), user["id"], "findy1234")
            )
            self.assertTrue(delete_findy2_user_data(data_path))
            self.assertTrue(delete_user_media(str(media_root), user["id"]))

            with open(auth_path, "r", encoding="utf-8") as file:
                self.assertEqual(json.load(file)["users"], [])
            self.assertFalse(os.path.exists(data_path))
            self.assertFalse((media_root / user["id"]).exists())
            self.assertIsNone(restore_session(str(auth_path), str(session_path)))

    def test_social_providers_merge_into_one_integrated_account(self):
        with tempfile.TemporaryDirectory() as directory:
            auth_path = str(Path(directory) / "users.json")
            account_ids = []
            for provider in ("naver", "kakao", "google", "apple"):
                user = social_login_or_register(
                    auth_path,
                    {
                        "provider": provider,
                        "providerUserId": f"{provider}-member-1",
                        "findyUserId": "user_findy_integrated_1",
                        "email": "member@findy.test",
                        "emailVerified": True,
                        "nickname": "통합회원",
                    },
                )
                account_ids.append(user["id"])

            self.assertEqual(set(account_ids), {"user_findy_integrated_1"})
            self.assertEqual(
                {item["provider"] for item in user["identities"]},
                {"naver", "kakao", "google", "apple"},
            )

    def test_verified_social_email_links_existing_email_account(self):
        with tempfile.TemporaryDirectory() as directory:
            auth_path = str(Path(directory) / "users.json")
            email_user = register_user(
                auth_path,
                "existing@findy.test",
                "김기존",
                "기존회원",
                "findy1234",
                phone_number="010-3333-4444",
                phone_verified=True,
            )
            social_user = social_login_or_register(
                auth_path,
                {
                    "provider": "google",
                    "providerUserId": "google-existing-1",
                    "findyUserId": "remote-existing-1",
                    "email": "existing@findy.test",
                    "emailVerified": True,
                    "nickname": "기존회원",
                },
            )
            self.assertEqual(social_user["id"], email_user["id"])
            self.assertEqual(social_user["remoteUserId"], "remote-existing-1")

    def test_remote_session_and_gateway_account_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session_path = root / "session.json"
            gateway.DATABASE_PATH = root / "gateway.db"
            with gateway._database() as connection:
                connection.execute(
                    "insert into accounts(id, email, nickname, created_at) values (?, ?, ?, ?)",
                    ("user_gateway_1", "gateway@findy.test", "게이트웨이회원", 1),
                )

            remote_token = gateway._create_session("user_gateway_1")
            create_session(
                str(session_path),
                {"id": "user_gateway_1"},
                remote_session_token=remote_token,
            )
            self.assertEqual(
                read_remote_session_token(str(session_path)),
                remote_token,
            )

            response = TestClient(gateway.app).delete(
                "/v1/account",
                headers={"Authorization": f"Bearer {remote_token}"},
            )
            self.assertEqual(response.status_code, 200)
            with gateway._database() as connection:
                account = connection.execute(
                    "select id from accounts where id = ?",
                    ("user_gateway_1",),
                ).fetchone()
            self.assertIsNone(account)

    def test_gateway_links_provider_to_current_account_and_blocks_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gateway.DATABASE_PATH = root / "gateway-link.db"
            with gateway._database() as connection:
                connection.execute(
                    "insert into accounts(id, email, nickname, created_at) values (?, ?, ?, ?)",
                    ("user_link_1", "one@findy.test", "회원1", 1),
                )
                connection.execute(
                    "insert into accounts(id, email, nickname, created_at) values (?, ?, ?, ?)",
                    ("user_link_2", "two@findy.test", "회원2", 1),
                )

            identity = {
                "provider": "naver",
                "providerUserId": "naver-link-member",
                "email": "one@findy.test",
                "emailVerified": True,
                "nickname": "회원1",
            }
            account_id = gateway._resolve_findy_account(
                identity,
                preferred_account_id="user_link_1",
            )
            self.assertEqual(account_id, "user_link_1")
            with self.assertRaises(RuntimeError):
                gateway._resolve_findy_account(
                    identity,
                    preferred_account_id="user_link_2",
                )


if __name__ == "__main__":
    unittest.main()
