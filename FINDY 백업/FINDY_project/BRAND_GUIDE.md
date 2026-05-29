# FINDY 공식 브랜드 컬러 가이드

> Find Your Beauty
> 사용자 맞춤형 뷰티/스타일 아티스트 추천 서비스

## 컬러 팔레트

| 역할 | HEX | 용도 |
|---|---|---|
| 메인 (Main) | `#AE8F6F` | 브랜드 시그니처 모카 |
| 서브 (Sub) | `#E6D7C8` | 보조 표면, 카드 액센트 |
| 포인트 (Point) | `#8B6B4F` | 강조/대비 포인트 |
| 언한 포인트 (Soft Point) | `#F5EEE7` | 옅은 강조 배경 (컴포넌트 내부 accent용) |
| 배경 (Background) | `#FFFFFF` | 앱 전체 배경 (미니멀 화이트 공식 채택) |
| 텍스트 (Text) | `#2C2A28` | 본문 다크 |
| 강조 텍스트 (Text Strong) | `#1A1A1A` | 헤드라인, 강조 |
| 보조 텍스트 (Subtext) | `#9A9189` | 서브 카피, 메타 |

## Theme 스펙

```python
# Flet ThemeData
color_scheme_seed = "#AE8F6F"
scaffold_background_color = "#FFFFFF"   # 공식 배경: 미니멀 화이트
card_theme = CardTheme(color="#FFFFFF")
highlight_color = "#8B6B4F"
```

## 컬러 토큰 (components/layout.py)

| 토큰 | HEX | 용도 |
|---|---|---|
| `MAIN_COLOR` | `#AE8F6F` | 버튼, 액센트, 브랜드 포인트 |
| `MAIN_COLOR_DARK` | `#8B6B4F` | 호버, 포커스, 강조 |
| `MAIN_COLOR_SOFT` | `#F5EEE7` | 칩 배경, 인풋 배경, 소프트 accent |
| `SUB_COLOR` | `#E6D7C8` | 카드 보더, 구분선 accent |
| `BG_COLOR` | `#FFFFFF` | scaffold 배경 ✓ 공식 |
| `SURFACE_COLOR` | `#FFFFFF` | 카드, 시트 표면 |
| `CARD_COLOR` | `#FFFFFF` | 카드 배경 |
| `TEXT_COLOR` | `#2C2A28` | 본문 텍스트 |
| `TEXT_STRONG` | `#1A1A1A` | 헤드라인 |
| `SUBTEXT_COLOR` | `#9A9189` | 보조 텍스트 |
| `MUTED_TEXT_COLOR` | `#BDB4AB` | 비활성, hint |
| `BORDER_COLOR` | `#ECE5DB` | 테두리 |
| `DIVIDER_COLOR` | `#F1ECE4` | 구분선 |
| `CHIP_BG` | `#F7F2EC` | 칩/태그 배경 |
| `INPUT_BG` | `#FAF7F2` | 인풋 필드 배경 |

## 로고 자산

`assets/` 폴더에 다음 파일이 있어야 합니다.

- `findy_opening_screen.png` — 쌍안경 + FINDY + "Find Your Beauty" 태그라인 (오프닝용)
- `findy_login_logo_transparent.png` — 쌍안경 + FINDY 워드마크 (로그인 헤더용)
- `findy_app_icon.png` — 흰 배경 라운드 사각 안 쌍안경 마크 (앱 아이콘용)
- `findy_logo_with_tagline.png` — 쌍안경 + "Find Your Beauty" (보조 사용)

## 서체

`assets/` 폴더에 Pretendard TTF 파일이 있어야 합니다.

| 파일명 | 용도 |
|---|---|
| `Pretendard-Regular.ttf` | `APP_FONT` — 기본 서체 |
| `Pretendard-Bold.ttf` | `APP_FONT_BOLD` — 강조, 버튼 |
| `Pretendard-Medium.ttf` | 중간 굵기 텍스트 |
| `Pretendard-SemiBold.ttf` | 섹션 타이틀 |
| `Pretendard-Light.ttf` | 보조 설명 텍스트 |
| `Pretendard-ExtraBold.ttf` | 대형 헤드라인 |
| `Pretendard-Black.ttf` | 최대 강조 |
| `Pretendard-ExtraLight.ttf` | 극세 텍스트 |
| `Pretendard-Thin.ttf` | 장식용 초경량 |

```python
# FINDY324.py 폰트 등록 (이미 구현됨)
page.fonts = {
    "Pretendard": "assets/Pretendard-Regular.ttf",
    "Pretendard-Bold": "assets/Pretendard-Bold.ttf",
}
page.theme = ft.Theme(font_family="Pretendard")
```

## 배경색 정책

**공식 배경: `#FFFFFF` (미니멀 화이트)**

화이트 배경이 FINDY의 공식 배경으로 채택되었습니다.
`#F5EEE7` (소프트 베이지)는 배경이 아닌 컴포넌트 내부 accent 용도(`MAIN_COLOR_SOFT`)로만 사용합니다.

배경을 베이지로 변경하려면 `components/layout.py`의 `BG_COLOR = "#F5EEE7"` 한 줄만 수정하면 됩니다.
