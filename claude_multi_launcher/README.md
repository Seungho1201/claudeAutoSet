# Claude Code Multi Launcher

여러 개의 [Claude Code](https://docs.claude.com/en/docs/claude-code) 인스턴스를
한 번의 클릭으로 동시에 실행하는 Python GUI 애플리케이션입니다. **작업 폴더는
앱 상단에서 한 번만 지정**하면 모든 인스턴스가 그 폴더에서 함께 실행됩니다.
각 인스턴스에는 **역할**, **시스템 프롬프트**, **초기 작업 지시 프롬프트**,
(선택) **모델**을 미리 설정해두면, "작업 시작" 버튼 한 번으로 새 터미널 창들이
일제히 열리고 Claude Code가 그 컨텍스트로 시작됩니다.

## 사전 준비

1. **Python 3.10+** 설치
2. **Node.js + Claude Code CLI** 설치
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
   설치 후 터미널에서 `claude --version`이 동작해야 합니다.
3. (Linux의 경우) 다음 중 하나의 터미널 에뮬레이터가 PATH에 있어야 합니다:
   `gnome-terminal`, `xterm`, `konsole`
4. (Windows의 경우) Windows Terminal(`wt`)이 있으면 새 탭으로 열리고,
   없으면 기본 `cmd` 창이 사용됩니다.

## 설치

```bash
git clone <this-repo>
cd claude_multi_launcher
pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

처음 실행하면 `config.json`이 자동 생성되고 샘플 인스턴스 3개가 등록됩니다.

## 사용법

### 인스턴스 관리
- 등록된 인스턴스는 **카드 격자**로 표시되며, 한 줄에 들어갈 카드 수는 **인스턴스 수에
  맞춰 자동으로 조정**됩니다 — 2개면 각 50%, 3개면 각 33%, 4개면 각 25%로 가로 폭을
  세로선으로 균등 분할합니다. 5개 이상이면 한 줄에 4개씩 채우고 나머지는 다음 줄로 넘어갑니다.
- 카드 **세로 높이**는 **300px 고정**입니다. 동적으로 viewport에 맞추는 시도는
  `<Configure>` 이벤트와 카드 height 변경이 서로 트리거하여 height가 무한 증식
  되는 문제(끝내 Windows GDI의 `CreateDIBSection` 픽스맵 한계 초과 → `Tk_GetPixmap`
  에러)가 재현되어, 안정성을 위해 고정값으로 확정했습니다. 카드가 list_frame
  영역보다 높이가 작아 회색 여백이 생기더라도 의도된 동작입니다.
  카드 안의 아이콘과 이름은 inner frame에 묶여 항상 카드 가운데에 응집됩니다.
- 각 카드 좌상단에 활성화 체크박스, 중앙에 **클로드 마스코트 PNG 아이콘**(60×60,
  파일: `icon/icons8-클로드-96.png`), 하단에 **사용자가 지정한 이름**만 표시됩니다.
  역할/프롬프트 같은 상세 정보는 카드에 표시하지 않으며 수정 다이얼로그에서 확인합니다.
  Pillow가 설치되어 있지 않으면 글자 "C"로 폴백됩니다 — `pip install -r requirements.txt`로 설치 가능.
- **＋ 인스턴스 추가**: 새 인스턴스를 등록합니다.
- **✎ 수정**: 선택한 인스턴스를 수정합니다. 카드를 **더블클릭**해도 됩니다.
- **🗑 삭제**: 선택한 인스턴스를 삭제합니다. (확인 다이얼로그 표시)
- **우클릭**: 컨텍스트 메뉴(수정/복제/활성화 토글/삭제)
- **체크박스**: 클릭으로 활성화/비활성화 즉시 토글 (자동 저장)
- **카드 단일 클릭**: 선택 (강조 색상으로 표시)

### 실행
- **▶ 작업 시작**: 활성화된(체크된) 모든 인스턴스를 새 터미널 창에서 실행합니다.
- **■ 전체 종료**: 실행 중인 모든 `claude` 프로세스를 강제 종료합니다.

### 실행 로그
- 화면 하단의 **실행 로그** 영역은 기본적으로 **접혀 있습니다**.
- 라벨 우측의 **▼** 버튼을 누르면 펼쳐지고(`▲`로 바뀜), 다시 누르면 접힙니다.
- 접혀 있는 동안에도 로그는 내부에 누적되므로, 펼치는 순간 그동안의 로그가 한꺼번에 보입니다.

### 언어 (i18n)
- 헤더 우측의 **⚙ 설정** 버튼을 누르면 화면 하단에 설정 패널이 펼쳐집니다.
- 패널에서 **한국어 / English / 日本語** 중 하나를 선택하면 즉시 모든 UI 텍스트가
  해당 언어로 갱신됩니다 (앱 재시작 불필요).
- 선택한 언어는 `config.json`의 `language` 필드(`ko`/`en`/`ja`)에 저장되어
  다음 실행에도 유지됩니다.
- 등록된 인스턴스의 이름·역할·프롬프트는 사용자 데이터로 보고 번역하지 않습니다.

### 레이아웃 / 창 상태 (Windows Terminal 전용)
- **레이아웃**
  - `탭으로 (한 창)` — 한 개의 wt 창에 인스턴스마다 새 탭
  - `세로 분할 (좌우)` — 한 개의 창에 좌우로 **균등 분할** (1/N씩)
  - `가로 분할 (상하)` — 한 개의 창에 위아래로 **균등 분할** (1/N씩)
  - `각각 별창` — 인스턴스마다 새 wt 창
- **창 상태**: `기본` / `최대화` / `전체화면`
- 위 옵션은 Windows Terminal(`wt`)이 PATH에 있을 때만 적용됩니다.
  `wt`가 없으면 인스턴스마다 클래식 `cmd` 창이 따로 뜹니다.

#### 분할 패널 크기 / 포커스 단축키 (Windows Terminal 안에서)
실행된 wt 창에서는 마우스 드래그로 패널 폭을 조절할 수 없습니다. 다음 키보드
단축키를 사용하세요.

| 단축키 | 동작 |
| --- | --- |
| `Alt + Shift + ←` / `→` | 활성 패널 가로 폭 축소/확대 |
| `Alt + Shift + ↑` / `↓` | 활성 패널 세로 폭 축소/확대 |
| `Alt + ←` / `→` / `↑` / `↓` | 활성 패널 포커스 이동 |
| `Ctrl + Shift + W` | 활성 패널 닫기 |
| `F11` | 전체화면 토글 |

각 터미널에서는 다음 명령이 실행됩니다.
```
cd "{working_directory}" && claude --append-system-prompt "{system_prompt}" "{initial_prompt}"
```
모델을 지정한 경우 `--model "{model}"`이 추가됩니다.

## 설정 파일 (`config.json`)

스크립트와 같은 디렉토리에 저장되며, GUI에서 변경할 때마다 자동 저장됩니다.

```json
{
  "working_directory": "C:\\path\\to\\project",
  "layout_mode": "tabs",
  "window_state": "normal",
  "language": "ko",
  "instances": [
    {
      "name": "프론트엔드 담당",
      "role": "React 개발자",
      "system_prompt": "당신은 React/TypeScript 전문가입니다...",
      "initial_prompt": "현재 프로젝트의 컴포넌트 구조를 살펴보고...",
      "model": "",
      "enabled": true
    }
  ]
}
```

`language`는 `"ko"`, `"en"`, `"ja"` 중 하나이며 ⚙ 설정 패널에서 변경됩니다. 잘못된 값이면 `"ko"`로 폴백됩니다.

> 구버전(`working_directory`가 인스턴스마다 들어 있던 형식)은 첫 실행 시 자동으로
> 새 형식으로 마이그레이션됩니다.

## 파일 구조

```
claude_multi_launcher/
├── main.py              # 진입점 + 메인 GUI (설정 패널, 카드 격자 포함)
├── instance_dialog.py   # 인스턴스 추가/수정 다이얼로그
├── launcher.py          # OS별 터미널 실행 로직
├── config_manager.py    # 설정 파일 입출력 + 데이터 모델
├── i18n.py              # 다국어(ko/en/ja) 번역 테이블 + t() 함수
├── icon/                # 카드 안에 표시할 클로드 마스코트 PNG
│   └── icons8-클로드-96.png
├── config.json          # 설정 파일 (최초 실행 시 자동 생성)
├── requirements.txt
└── README.md
```

## 트러블슈팅

| 증상 | 원인 / 해결 |
| --- | --- |
| `claude CLI를 찾을 수 없습니다` | `npm install -g @anthropic-ai/claude-code` 후 새 셸에서 실행 |
| 터미널 창은 뜨는데 곧바로 닫힘 | 작업 디렉토리 경로가 틀렸을 가능성. 인스턴스 수정에서 경로 확인 |
| Linux에서 `터미널 실행 파일을 찾을 수 없음` | `sudo apt install gnome-terminal` 등으로 터미널 에뮬레이터 설치 |
| `config.json`이 손상됨 알림 | 파일을 백업한 뒤 삭제하면 다음 실행 시 새로 생성됨 |
| 한글이 깨져 보임 | Windows Terminal 또는 UTF-8 지원 콘솔 사용 권장 |
| 분할 패널 크기를 마우스로 못 줄임 | Windows Terminal은 마우스 리사이즈 미지원. `Alt+Shift+←/→/↑/↓` 단축키로 조절 (위 "단축키" 표 참고) |

## 라이선스

MIT
