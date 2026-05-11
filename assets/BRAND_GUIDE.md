# FINDY 공식 브랜드 컬러 가이드

> Find Your Beauty
> 사용자 맞춤형 뷰티/스타일 아티스트 추천 서비스

## 컬러 팔레트

| 역할 | HEX | 용도 |
|---|---|---|
| 메인 (Main) | `#AE8F6F` | 브랜드 시그니처 모카 |
| 서브 (Sub) | `#E6D7C8` | 보조 표면, 카드 액센트 |
| 포인트 (Point) | `#8B6B4F` | 강조/대비 포인트 |
| 언한 포인트 (Soft Point) | `#F5EEE7` | 옅은 강조 배경 |
| 텍스트 (Text) | `#4A3A2A` | 본문 다크 |
| 보조 텍스트 (Subtext) | `#9C8A78` | 서브 카피, 메타 |

## Theme 스펙

```python
# Flet ThemeData
color_scheme_seed = "#AE8F6F"
scaffold_background_color = "#F5EEE7"
card_theme = CardTheme(color="#E6D7C8")
highlight_color = "#8B6B4F"
```

## 로고 자산

assets 폴더에 다음 파일이 있어야 합니다(없으면 사용자가 추가).

- `findy_app_icon.png` — 흰 배경 라운드 사각 안 쌍안경 마크 (앱 아이콘용)
- `findy_login_logo_transparent.png` — 쌍안경 + FINDY 워드마크 (로그인 헤더용, 이미 존재)
- `findy_opening_screen.png` — 쌍안경 + FINDY + "Find Your Beauty" 태그라인 (오프닝용, 이미 존재)
- `findy_logo_with_tagline.png` — 쌍안경 + "Find Your Beauty" (보조 사용)

## 현재 코드와의 차이 (참고)

메인/포인트 컬러는 공식 가이드와 정확히 일치하며, 배경만 미니멀 화이트로 운영합니다.

| 토큰 | 공식 가이드 | 현재 코드 | 비고 |
|---|---|---|---|
| MAIN_COLOR | `#AE8F6F` | `#AE8F6F` | 공식 일치 ✓ |
| MAIN_COLOR_DARK | `#8B6B4F` | `#8B6B4F` | 공식 일치 ✓ |
| MAIN_COLOR_SOFT | `#F5EEE7` | `#F5EEE7` | 공식 일치 ✓ |
| SUB_COLOR | `#E6D7C8` | `#E6D7C8` | 공식 일치 ✓ (카드 액센트로 활용 가능) |
| BG_COLOR | `#F5EEE7` | `#FFFFFF` | 미니멀 화이트 채택 |
| TEXT_COLOR | `#4A3A2A` | `#2C2A28` | 화이트 BG 대비 콜드 다크 |
| SUBTEXT_COLOR | `#9C8A78` | `#9A9189` | 거의 동일 |

배경까지 공식 베이지(#F5EEE7)로 회귀하고 싶을 땐 `components/layout.py`의 `BG_COLOR`만 바꾸면 됩니다.
