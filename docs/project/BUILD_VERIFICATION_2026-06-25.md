# FINDY2 빌드 검증 기록

검증일: 2026년 6월 25일  
앱 버전: `0.1.0 (1)`

## Android 결과

- APK: `build/apk/app-release.apk`
- APK 크기: `99,312,322 bytes`
- APK SHA-256: `d39faa28e6371c93d1984da3930c9838cb0bdd8fe3911880d4441a4f5be25035`
- AAB: `build/aab/app-release.aab`
- AAB 크기: `99,225,769 bytes`
- AAB SHA-256: `d8c5e95e73a9716b649560ddd4445cf587993068f8b4b3efaf8ca3ab899a2976`

검증된 메타데이터:

- Application ID: `com.findybeauty.findy2`
- Application label: `FINDY2`
- Version name: `0.1.0`
- Version code: `1`
- Minimum SDK: `21`
- Target SDK: `35`
- Release 권한: 인터넷, Android 시스템 사진 선택 권한
- 카메라, 마이크, 위치 권한: 없음
- 현재 코드 기준 다음 모바일 빌드부터 선택 위치 권한을 포함합니다.
- 네이버, 카카오, Google, Apple 통합 로그인 UI와 인증 게이트웨이 클라이언트 포함
- 설정 내 연결된 계정 관리와 공급자 연결 충돌 보호 포함

두 파일 모두 JAR 서명 무결성 검사를 통과했습니다.

## 서명 주의

현재 산출물은 Android Debug 인증서로 서명되어 기기 테스트에만 사용합니다. Google Play 업로드 전 FINDY 전용 업로드 키를 생성하고 `pyproject.toml` 또는 빌드 명령의 Android signing 설정으로 다시 빌드해야 합니다.

## iOS 상태

- Xcode 26.5 설치 확인
- CocoaPods 미설치
- Apple Developer Team ID, 인증서와 Provisioning Profile 미설정

iOS 아카이브와 IPA 검증은 위 항목을 준비한 뒤 진행합니다.

## 자동 검증

다음 검증을 통과했습니다.

- Python 컴파일
- 앱 자산, 라우팅과 문서 스모크 테스트
- 인증/계정 삭제/사용자 데이터/미디어 삭제 서비스 테스트
- 네 공급자 통합회원 병합과 인증 게이트웨이 계정 삭제 테스트
- 기존 FINDY 계정에 공급자 추가 연결 및 중복 연결 차단 테스트
- 인증 게이트웨이 전용 가상환경 설치와 `/health` 실제 실행 검증
- `git diff --check`
