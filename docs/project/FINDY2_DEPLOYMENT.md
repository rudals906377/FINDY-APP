# FINDY2 배포 가이드

기준 버전: `0.1.0`  
기준일: 2026년 6월 25일

## 배포 진입점

- Flet 진입점: `main.py`
- 실제 앱: `python_files/FINDY2.py`
- 배포 설정: `pyproject.toml`
- 아이콘 원본: `assets/app_logo/app_findy_logo_mark.png`
- 생성 아이콘: `assets/icon.png`
- 생성 스플래시: `assets/splash.png`

## 사전 검증

```bash
python3 scripts/generate_release_assets.py
python3 python_files/test_findy2_services.py
python3 python_files/smoke_test.py
git diff --check
```

## 빌드

```bash
scripts/build_findy2.sh apk
scripts/build_findy2.sh aab
scripts/build_findy2.sh ipa
```

iOS는 Apple Developer Team ID, 배포 인증서와 Provisioning Profile이 추가로 필요합니다.

## 현재 메타데이터

- 제품명: `FINDY2`
- 프로젝트명: `findy2`
- 번들 ID 초안: `com.findybeauty.findy2`
- 버전: `0.1.0`
- 빌드 번호: `1`
- 요청 권한: 사진 보관함

번들 ID는 앱을 스토어에 최초 등록하기 전에 실제 소유 가능한 값으로 최종 확정해야 합니다.

## 공개 배포 차단 항목

- 운영자 정식 명칭, 주소와 문의 이메일
- 개인정보 처리방침과 이용약관의 공개 HTTPS URL
- 외부 계정 삭제 요청 HTTPS URL
- Apple Developer 및 Google Play Console 계정
- Android 업로드 키와 안전한 보관 위치
- iOS Team ID, 인증서와 Provisioning Profile
- 서버 데이터 저장소와 운영자 신고 검토 도구
- 미성년자 이용 정책과 스토어 연령 등급

## 최근 빌드 검증

2026년 6월 25일 APK와 AAB 생성 및 메타데이터 검증을 완료했습니다. 자세한 결과와 SHA-256은 `docs/project/BUILD_VERIFICATION_2026-06-25.md`를 확인합니다.

현재 산출물은 Debug 인증서로 서명되어 테스트 전용입니다.
