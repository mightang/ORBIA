TERMPROJECT/
├─ app.py                          # 메인 실행 진입점 (씬 매니저)
├─ game.py                         # 단일 스테이지 디버그 런처
├─ settings.py                     # 전역 상수 / 색상 / 해상도 설정
├─ save.json                       # 스테이지 진행도 / 최대 해금 정보 저장
│
├─ assets/
│  ├─ fonts/
│  │  └─ PretendardVariable.ttf    # 기본 UI/게임 폰트
│  ├─ images/                      # (선택) UI 아이콘, 튜토리얼 이미지 등
│  └─ sounds/
│     ├─ main.ogg                  # 타이틀·메인 BGM
│     ├─ basic.ogg                 # basic 스테이지 BGM
│     ├─ intermediate_1.ogg        # intermediate 1~6 BGM
│     ├─ intermediate_2.ogg        # intermediate 7~12 BGM
│     ├─ advance_1.ogg             # advance 1~6 BGM
│     ├─ advance_2.ogg             # advance 7~12 BGM
│     ├─ advance_3.ogg             # advance 13~18 BGM
│     ├─ tile_click_correct.wav    # 타일 정답 클릭 효과음
│     ├─ tile_click_false.wav      # 타일 오답 클릭(실수) 효과음
│     └─ ui_click.wav              # 버튼 UI 클릭 효과음
│
├─ core/                           # 게임 로직 / 씬 / UI
│  ├─ board.py                     # 보드 상태 / 규칙 / 실수 카운트 / 승리 판정
│  ├─ grid.py                      # 육각 그리드 구조 및 이웃 계산
│  ├─ hexmath.py                   # 육각 좌표 <-> 픽셀 좌표 변환
│  ├─ render.py                    # 보드/HUD/모달/별 표시 등 렌더링
│  ├─ scenes.py                    # Title / LevelSelect / Gameplay / Options 씬
│  └─ ui.py                        # Button, Slider, 간단한 라벨 등 UI 컴포넌트
│
├─ animations/
│  └─ title_space.py               # 타이틀·레벨 선택에서 사용하는 우주 배경 애니메이션
│
└─ stages/                         # 스테이지 데이터 (JSON)
   ├─ tutorial/
   │  └─ 001.json                  # 튜토리얼 스테이지
   ├─ basic/                       # basic 6스테이지 (2~7번에 매핑)
   │  ├─ 001.json
   │  ├─ 002.json
   │  ├─ 003.json
   │  ├─ 004.json
   │  ├─ 005.json
   │  └─ 006.json
   ├─ intermediate/                # intermediate 12스테이지 (8~19번)
   │  ├─ 001.json
   │  └─ … 012.json
   └─ advance/                     # advance 18스테이지 (20~37번)
      ├─ 001.json
      └─ … 018.json
