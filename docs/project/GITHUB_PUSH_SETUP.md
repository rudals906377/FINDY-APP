# GitHub 푸시 준비

현재 원격 저장소는 아래 주소입니다.

```text
https://github.com/rudals906377/FINDY-APP.git
```

현재 로컬 커밋은 만들어져 있지만, 이 컴퓨터에서 GitHub 인증이 아직 잡히지 않아 푸시가 막힐 수 있습니다.

## 1. 가장 쉬운 방법: GitHub CLI

```bash
brew install gh
gh auth login
git push origin main
```

로그인 선택지는 보통 아래처럼 고르면 됩니다.

```text
GitHub.com
HTTPS
Login with a web browser
```

## 2. SSH 키 방식

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
pbcopy < ~/.ssh/id_ed25519.pub
```

복사된 공개키를 GitHub > Settings > SSH and GPG keys에 추가한 뒤 원격 주소를 SSH로 바꿉니다.

```bash
git remote set-url origin git@github.com:rudals906377/FINDY-APP.git
git push origin main
```

## 3. Personal Access Token 방식

GitHub에서 Fine-grained token 또는 Classic token을 만들고, `Contents: Read and write` 권한을 줍니다.

```bash
git push origin main
```

비밀번호를 물으면 GitHub 비밀번호가 아니라 발급받은 토큰을 입력합니다.

## 4. 푸시 전 확인

```bash
git status --short
PYTHONPYCACHEPREFIX=/private/tmp/findy_pycache python3 python_files/smoke_test.py
PYTHONPYCACHEPREFIX=/private/tmp/findy_pycache python3 python_files/test_findy2_services.py
git diff --check
```

## 5. 이번에 확인된 문제

- `gh` 명령어가 설치되어 있지 않습니다.
- SSH 인증은 `Permission denied (publickey)` 상태입니다.
- HTTPS 원격 저장소는 사용자명/토큰 입력이 필요합니다.
