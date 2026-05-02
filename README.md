# Claude Code Multi Launcher

여러 개의 [Claude Code](https://docs.claude.com/en/docs/claude-code) 인스턴스를
역할·프롬프트별로 미리 등록해두고, 버튼 한 번으로 같은 작업 폴더에서
**동시에 실행**하는 Python GUI 런처입니다.

- 인스턴스마다 **역할 / 시스템 프롬프트 / 초기 지시 / (선택) 모델** 미리 등록
- **작업 폴더는 앱 상단에서 한 번만 지정** → 모든 인스턴스가 그 폴더에서 시작
- Windows Terminal에서 **탭 / 세로 분할 / 가로 분할 / 별창** 레이아웃 선택
- 분할 시 인스턴스 수에 맞춰 **1/N 균등 폭**으로 자동 분할
- Windows / macOS / Linux 지원

> 자세한 옵션·트러블슈팅은
> [`claude_multi_launcher/README.md`](claude_multi_launcher/README.md) 참고.

---

## 사전 준비

| | 필요한 것 |
| --- | --- |
| 공통 | Python 3.10+ |
| 공통 | [Claude Code CLI](https://docs.claude.com/en/docs/claude-code) — `npm install -g @anthropic-ai/claude-code` |
| Windows | Windows Terminal(`wt`)이 있으면 탭/분할 사용 가능. 없으면 인스턴스마다 `cmd` 창 |
| macOS | 기본 Terminal.app 사용 |
| Linux | `gnome-terminal` / `xterm` / `konsole` 중 하나가 PATH에 있어야 함 |

설치 후 셸에서 `claude --version`이 동작해야 합니다.

---

## 설치 & 실행

```bash
git clone https://github.com/Seungho1201/claudeAutoSet.git
cd claudeAutoSet/claude_multi_launcher
pip install -r requirements.txt
python main.py
```

처음 실행하면 같은 폴더에 `config.json`이 자동 생성되고 샘플 인스턴스 3개가 등록됩니다.

---

## 사용 방법

### 1) 작업 폴더 지정
앱 상단의 **작업 폴더** 입력 칸에 모든 인스턴스가 시작할 디렉터리를 지정합니다.
한 번 지정하면 `config.json`에 저장되어 다음 실행에도 유지됩니다.

### 2) 인스턴스 등록·관리
| 버튼 / 동작 | 설명 |
| --- | --- |
| **＋ 인스턴스 추가** | 새 인스턴스 등록 (이름·역할·시스템 프롬프트·초기 지시·모델) |
| **✎ 수정** *(또는 항목 더블클릭)* | 선택한 인스턴스 편집 |
| **🗑 삭제** | 선택한 인스턴스 삭제 (확인 다이얼로그) |
| 우클릭 메뉴 | 수정 / 복제 / 활성화 토글 / 삭제 |
| 체크박스 | 클릭으로 활성화·비활성화 즉시 토글 (자동 저장) |

각 인스턴스에는 다음 4개 필드를 채울 수 있습니다.

- **이름**: 터미널 탭/창 제목
- **역할**: 메모용 (예: "백엔드 개발자")
- **시스템 프롬프트**: `claude --append-system-prompt`로 전달
- **초기 작업 지시 프롬프트**: `claude` 첫 메시지로 전달
- **모델** *(선택)*: `claude --model "<model-id>"`로 전달. 비우면 기본 모델

### 3) 레이아웃 / 창 상태 선택 *(Windows Terminal 한정)*

| 레이아웃 | 동작 |
| --- | --- |
| `탭으로 (한 창)` | 한 wt 창에 인스턴스마다 새 탭 |
| `세로 분할 (좌우)` | 한 창에 좌우로 균등 분할 (1/N씩) |
| `가로 분할 (상하)` | 한 창에 위아래로 균등 분할 (1/N씩) |
| `각각 별창` | 인스턴스마다 새 wt 창 |

**창 상태**: `기본` / `최대화` / `전체화면`.
`wt`가 없으면 옵션은 무시되고 클래식 `cmd` 창이 인스턴스마다 따로 뜹니다.

### 4) 작업 시작 / 종료
- **▶ 작업 시작** — 활성화된(체크된) 모든 인스턴스를 새 터미널에서 일괄 실행
- **■ 전체 종료** — 실행 중인 모든 `claude` 프로세스 강제 종료

각 터미널에서는 다음 명령이 실행됩니다.
```
cd "{working_directory}" && claude --append-system-prompt "{system_prompt}" "{initial_prompt}"
```
모델을 지정한 경우 `--model "{model}"`이 추가됩니다.

### 5) 실행된 wt 창 안에서 — 패널 크기·포커스 단축키

Windows Terminal은 마우스로 패널 크기를 못 줄입니다. 키보드를 사용하세요.

| 단축키 | 동작 |
| --- | --- |
| `Alt + Shift + ←` / `→` | 활성 패널 가로 폭 축소/확대 |
| `Alt + Shift + ↑` / `↓` | 활성 패널 세로 폭 축소/확대 |
| `Alt + ←` / `→` / `↑` / `↓` | 활성 패널 포커스 이동 |
| `Ctrl + Shift + W` | 활성 패널 닫기 |
| `F11` | 전체화면 토글 |

---

## 설정 파일 (`config.json`)

스크립트와 같은 디렉터리에 저장되며 GUI에서 변경할 때마다 자동 저장됩니다.

```json
{
  "working_directory": "C:\\path\\to\\project",
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

> 구버전(`working_directory`가 인스턴스마다 들어 있던 형식)은 첫 실행 시 자동으로
> 새 형식으로 마이그레이션됩니다.

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
| --- | --- |
| `claude CLI를 찾을 수 없습니다` | `npm install -g @anthropic-ai/claude-code` 후 새 셸에서 실행 |
| 터미널 창은 뜨는데 곧바로 닫힘 | 작업 디렉토리 경로가 틀렸을 가능성. 인스턴스 수정에서 경로 확인 |
| Linux에서 `터미널 실행 파일을 찾을 수 없음` | `sudo apt install gnome-terminal` 등으로 터미널 에뮬레이터 설치 |
| `config.json`이 손상됨 알림 | 파일 백업 후 삭제하면 다음 실행 시 새로 생성됨 |
| 한글이 깨져 보임 | Windows Terminal 또는 UTF-8 지원 콘솔 사용 권장 |
| 분할 패널 크기를 마우스로 못 줄임 | Windows Terminal은 마우스 리사이즈 미지원. 위 "단축키" 표 참고 |

---

## 파일 구조

```
claudeAutoSet/
├── README.md                          # 이 파일 (GitHub 진입점)
└── claude_multi_launcher/
    ├── main.py                        # 진입점 + 메인 GUI
    ├── instance_dialog.py             # 인스턴스 추가/수정 다이얼로그
    ├── launcher.py                    # OS별 터미널 실행 로직
    ├── config_manager.py              # 설정 파일 입출력 + 데이터 모델
    ├── config.json                    # 설정 파일 (최초 실행 시 자동 생성)
    ├── requirements.txt
    └── README.md                      # 자세한 문서
```

---

## 라이선스

MIT
