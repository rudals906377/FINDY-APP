from typing import Any, Dict, Optional

import httpx


DEFAULT_TIMEOUT_SECONDS = 5.0


def _result(ok: bool, data: Any = None, error: str = "") -> Dict[str, Any]:
    return {"ok": ok, "data": data, "error": error}


class FindyApiClient:
    """Small synchronous client for the optional FINDY2 운영 API.

    The app must remain fully usable in local-only mode, so every method returns
    a simple result object instead of raising network errors into the UI.
    """

    def __init__(self, base_url: str = "", admin_api_key: str = "", timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self.base_url = (base_url or "").rstrip("/")
        self.admin_api_key = admin_api_key or ""
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    def _url(self, path: str) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{normalized}"

    def _headers(self, admin: bool = False) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if admin and self.admin_api_key:
            headers["X-FINDY-ADMIN-KEY"] = self.admin_api_key
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        admin: bool = False,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.configured:
            return _result(False, error="FINDY2_API_URL이 설정되지 않아 로컬 모드로 동작 중이에요.")
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method,
                    self._url(path),
                    headers=self._headers(admin=admin),
                    json=json,
                    params=params,
                )
                response.raise_for_status()
                if not response.content:
                    return _result(True, data={})
                return _result(True, data=response.json())
        except httpx.HTTPStatusError as error:
            return _result(False, error=f"API 오류 {error.response.status_code}: {error.response.text[:160]}")
        except (httpx.HTTPError, ValueError) as error:
            return _result(False, error=str(error))

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def list_notices(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/notices")

    def create_notice(self, title: str, body: str, category: str = "notice") -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v1/admin/notices",
            admin=True,
            json={"title": title, "body": body, "category": category, "isPinned": False},
        )

    def list_reports(self, status: str = "pending") -> Dict[str, Any]:
        params = {"status": status} if status else None
        return self._request("GET", "/v1/admin/reports", admin=True, params=params)

    def update_report(self, report_id: str, status: str, admin_memo: str = "") -> Dict[str, Any]:
        return self._request(
            "PATCH",
            f"/v1/admin/reports/{report_id}",
            admin=True,
            json={"status": status, "adminMemo": admin_memo},
        )

    def admin_dashboard(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/admin/dashboard", admin=True)

    def list_admin_content(self, status: str = "") -> Dict[str, Any]:
        params = {"status": status} if status else None
        return self._request("GET", "/v1/admin/content", admin=True, params=params)

    def update_content_status(
        self,
        target_type: str,
        target_id: str,
        status: str,
        admin_memo: str = "",
    ) -> Dict[str, Any]:
        return self._request(
            "PATCH",
            f"/v1/admin/content/{target_type}/{target_id}/status",
            admin=True,
            json={"status": status, "adminMemo": admin_memo},
        )

    def point_summary(self, user_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/points/{user_id}")

    def adjust_points(self, user_id: str, amount: int, reason: str = "운영자 조정") -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v1/points/admin/adjust",
            admin=True,
            json={"userId": user_id, "amount": int(amount), "reason": reason},
        )
