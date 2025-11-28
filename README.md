# ORBIA  
Hexagonal Logic Puzzle Game

<p align="center">
  <img src="assets/images/orbia_icon.png" width="240" style="border-radius: 12px;">
</p>

---

## 소개

**ORBIA**는 육각형 좌표계를 기반으로 한 SF 스타일의 **논리 퍼즐 게임**입니다.  
육각 구조 특유의 시각적 정보 전달성, 간결한 규칙, 차분한 UI 디자인을 특징으로 하며  
총 37개의 스테이지를 제공하는 캠페인 형식의 퍼즐 게임입니다.

---

## 특징

### ● 육각형 퍼즐 구조
- 6방향 이웃을 기반으로 한 논리 추론  
- 사각형 기반 퍼즐보다 더 다양한 패턴 구성 가능

### ● 캠페인 기반 진행
- r = 0 ~ 3까지의 육각형 링으로 구성된 37개의 스테이지  
- 튜토리얼 → 쉬움 → 보통 → 어려움까지 점진적 난이도

### ● 연속 오픈(0 영역)
- 주변에 숫자가 없는 빈 타일을 열면 자동으로 확장 오픈  
- 직관적인 탐색 흐름 제공

### ● SF 기반 미니멀 UI
- 파스텔·차가운 색감의 화면 구성  
- HUD와 타일 렌더링 모두 명료함에 집중

---

## 설치 & 실행 방법

### 1) Python 3.10 이상 설치

버전 확인:

~~~bash
python --version
~~~

### 2) pygame 설치

~~~bash
pip install pygame
~~~

### 3) 실행

~~~bash
python app.py
~~~

타이틀 화면 → 스테이지 선택 → 게임 플레이 순으로 진행됩니다.

---

## 조작 방법

| 입력        | 기능                         |
|------------|------------------------------|
| 좌클릭     | 타일 오픈                    |
| 우클릭     | 깃발 표시                    |
| ESC        | 스테이지 선택으로 돌아가기   |
| 클리어 화면 | Retry / Menu / Next 버튼 제공 |

---

## 스테이지 구성

게임은 육각형 링 구조로 구성되어 있으며, 스테이지 수는 다음과 같습니다:

~~~text
r = 0  → 1 스테이지  
r = 1  → 6 스테이지  
r = 2  → 12 스테이지  
r = 3  → 18 스테이지  

총 37 스테이지
~~~

각 스테이지는 JSON 기반으로 구성됩니다.

예시:

~~~json
{
  "id": "003",
  "name": "Sector 1-3",
  "grid": { "shape": "hex", "width": 10, "height": 10 },
  "blocked": [[-5, 0], [-4, 1]],
  "mines": [[0, -2], [1, -2]],
  "start_revealed": [[0, 0]]
}
~~~

---

## 프로젝트 구조

## 프로젝트 구조

```text
TermProject/
├─ app.py
├─ settings.py
│
├─ animations/
│  ├─ init.py
│  ├─ game_hex_bg.py
│  ├─ scene_transition.py
│  ├─ stage_star_glow.py
│  ├─ tile_hover.py
│  ├─ tile_mistake.py
│  ├─ tile_reveal.py
│  └─ title_space.py
│
├─ assets/
│  ├─ fonts/
│  │  └─ PretendardVariable.ttf
│  │
│  ├─ images/
│  │  ├─ game_title.png
│  │  ├─ orbia_icon.png
│  │  │
│  │  ├─ README/
│  │  │  ├─ gameplay.png
│  │  │  ├─ levelselect.png
│  │  │  └─ title.png
│  │  │
│  │  └─ tutorial/
│  │     ├─ tuto_01.png
│  │     ├─ tuto_02.png
│  │     ├─ tuto_03.png
│  │     └─ tuto_04.png
│  │
│  └─ sounds/
│     ├─ advance_1.ogg
│     ├─ advance_2.ogg
│     ├─ advance_3.ogg
│     ├─ basic.ogg
│     ├─ intermediate_1.ogg
│     ├─ intermediate_2.ogg
│     ├─ main.ogg
│     ├─ tile_click_correct.wav
│     ├─ tile_click_false.wav
│     ├─ tile_hover.wav
│     └─ ui_click.wav
│
├─ core/
│  ├─ board.py
│  ├─ grid.py
│  ├─ hexmath.py
│  ├─ render.py
│  ├─ scenes.py
│  └─ ui.py
│
├─ saves/
│
└─ stages/
   ├─ tutorial/
   │  └─ 001.json
   │
   ├─ basic/
   │  ├─ 002.json
   │  ├─ 003.json
   │  ├─ 004.json
   │  ├─ 005.json
   │  ├─ 006.json
   │  └─ 007.json
   │
   ├─ intermediate/
   │  ├─ 008.json
   │  ├─ 009.json
   │  ├─ 010.json
   │  ├─ 011.json
   │  ├─ 012.json
   │  ├─ 013.json
   │  ├─ 014.json
   │  ├─ 015.json
   │  ├─ 016.json
   │  ├─ 017.json
   │  ├─ 018.json
   │  └─ 019.json
   │
   └─ advance/
      ├─ 020.json
      ├─ 021.json
      ├─ 022.json
      ├─ 023.json
      ├─ 024.json
      ├─ 025.json
      ├─ 026.json
      ├─ 027.json
      ├─ 028.json
      ├─ 029.json
      ├─ 030.json
      ├─ 031.json
      ├─ 032.json
      ├─ 033.json
      ├─ 034.json
      ├─ 035.json
      ├─ 036.json
      └─ 037.json
~~~
```
---

## 게임 플레이 화면
<p align="center">
  <img src="assets/images/README/title.png" width="240" style="border-radius: 12px;">
</p>
<p align="center">
  <img src="assets/images/README/gameplay.png" width="240" style="border-radius: 12px;">
</p>
<p align="center">
  <img src="assets/images/README/levelselect.png" width="240" style="border-radius: 12px;">
</p>

---

## 개발 내용 요약

- Python + pygame 기반  
- 육각형 좌표계(axial/cube) 구현  
- 보드 상태 및 숫자 단서 계산  
- 빈 영역 연속 오픈(플러드필)  
- 스테이지 JSON 로딩 및 관리  
- 타이틀 화면 / 스테이지 선택 / 플레이 화면 구현  
- 단일 스테이지 테스트용 런처(`game.py`) 제공  

---

## 라이선스

**[Font]**<br>
(https://noonnu.cc/font_page/694)

**[배경 음악]**<br>
(https://www.youtube.com/watch?v=7OQx3dMjBMQ&list=RDQMVI8r1aHT3yA&index=10)  
(https://www.youtube.com/watch?v=6RO7K4W-c9g&list=RDQMVI8r1aHT3yA&index=5)  
(https://www.youtube.com/watch?v=XMn4DA7UxFk&list=RDQMudcOVFF92x0&index=7)  
(https://www.youtube.com/watch?v=YUE2LoPlBs0&list=PLuqZTQ_5gsprXxxcIR8KeohOY4lM82m-Q&index=13)  
(https://www.youtube.com/watch?v=EVHet8oqWBo&list=PLuqZTQ_5gsprXxxcIR8KeohOY4lM82m-Q&index=19)  
(https://www.youtube.com/watch?v=sUXboASMRkc&list=PLuqZTQ_5gsprXxxcIR8KeohOY4lM82m-Q&index=42)

**[Click SFX]**<br>
(https://mixkit.co/free-sound-effects/)
