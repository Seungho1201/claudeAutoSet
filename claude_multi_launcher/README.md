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
- **＋ 인스턴스 추가**: 새 인스턴스를 등록합니다.
- **✎ 수정**: 선택한 인스턴스를 수정합니다. 항목을 **더블클릭**해도 됩니다.
- **🗑 삭제**: 선택한 인스턴스를 삭제합니다. (확인 다이얼로그 표시)
- **우클릭**: 컨텍스트 메뉴(수정/복제/활성화 토글/삭제)
- **체크박스**: 클릭으로 활성화/비활성화 즉시 토글 (자동 저장)

### 실행
- **▶ 작업 시작**: 활성화된(체크된) 모든 인스턴스를 새 터미널 창에서 실행합니다.
- **■ 전체 종료**: 실행 중인 모든 `claude` 프로세스를 강제 종료합니다.

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

## 파일 구조

```
claude_multi_launcher/
├── main.py              # 진입점 + 메인 GUI
├── instance_dialog.py   # 인스턴스 추가/수정 다이얼로그
├── launcher.py          # OS별 터미널 실행 로직
├── config_manager.py    # 설정 파일 입출력 + 데이터 모델
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

## 라이선스

MIT
