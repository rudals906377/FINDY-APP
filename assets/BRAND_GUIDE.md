# FINDY 브랜드 컬러 가이드

> Find Your Beauty

FINDY는 앱 전체에서 색상을 많이 쓰지 않고, 대표 포인트 컬러와 라인 컬러만으로 화면을 정리합니다.

## 핵심 원칙

- 대표색, 로고색, 선택 상태, 주요 버튼은 모두 `#8B6B4F`로 통일합니다.
- 카드, 입력창, 칩의 기본 배경은 흰색으로 유지합니다.
- 구분선과 카드 테두리는 `#E6D7C8`만 사용합니다.
- 보조 배경색을 별도로 늘리지 않고, 필요한 경우 흰색 배경 + 라인으로 구분합니다.
- 브랜드 로고는 텍스트로 직접 그리지 않고 기존 이미지 에셋을 사용합니다.

## 컬러 팔레트

| 역할 | HEX | 용도 |
|---|---|---|
| 대표 / 로고 / 포인트 | `#8B6B4F` | 로고, 주요 버튼, 선택 탭, 강조 아이콘 |
| 라인 / 구분선 | `#E6D7C8` | 카드 테두리, 입력창 테두리, 섹션 구분선 |
| 배경 / 카드 | `#FFFFFF` | 전체 배경, 카드, 기본 칩, 입력 필드 |
| 강한 텍스트 | `#1F1A17` | 제목, 핵심 정보 |
| 본문 텍스트 | `#2B2420` | 일반 본문 |
| 보조 텍스트 | `#786A62` | 설명, 메타 정보 |

## 앱 토큰

```python
LOGO_COLOR = "#8B6B4F"
MAIN_COLOR = "#8B6B4F"
MAIN_COLOR_DARK = "#8B6B4F"
MAIN_COLOR_SOFT = "#FFFFFF"
SUB_COLOR = "#E6D7C8"

BG_COLOR = "#FFFFFF"
SURFACE_COLOR = "#FFFFFF"
CARD_COLOR = "#FFFFFF"

TEXT_STRONG = "#1F1A17"
TEXT_COLOR = "#2B2420"
SUBTEXT_COLOR = "#786A62"
MUTED_TEXT_COLOR = "#B6AAA2"

CHIP_BG = "#FFFFFF"
BORDER_COLOR = "#E6D7C8"
DIVIDER_COLOR = "#E6D7C8"
INPUT_BG = "#FFFFFF"
```

## 로고 사용

앱에서 사용하는 로고는 `assets/app_logo`의 완성본을 기준으로 합니다.

- `app_findy_logo_vertical.png`
- `app_findy_logo_horizontal.png`
- `app_findy_logo_wordmark.png`
- `app_findy_logo_mark.png`
- `app_findy_opening_logo.png`

