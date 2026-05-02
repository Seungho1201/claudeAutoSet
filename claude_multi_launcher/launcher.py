"""Claude Code CLI를 새 터미널 창에서 실행하는 OS별 로직.

Windows에서 Windows Terminal(wt)이 있으면 단일 명령으로 모든 인스턴스를 띄우고
사용자가 선택한 레이아웃(탭/세로분할/가로분할/별창)과 창 상태(normal/maximized
/fullscreen)를 적용한다. wt가 없으면 클래식 cmd 창을 인스턴스마다 따로 띄운다.

핵심 함수:
- is_claude_cli_available(): claude CLI가 PATH에 있는지 검사
- launch_all(instances, working_directory, layout_mode, window_state)
- terminate_all()
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Tuple

from config_manager import Instance


@dataclass
class LaunchResult:
    """단일 인스턴스(또는 일괄 실행) 결과."""

    instance_name: str
    success: bool
    message: str


# ------------------------------------------------------------ 환경 검사 유틸
def is_claude_cli_available() -> bool:
    """claude CLI가 PATH에 설치되어 있는지 확인."""
    return shutil.which("claude") is not None


def _shell_escape_double_quotes(text: str) -> str:
    """터미널에 전달할 문자열에서 큰따옴표/백슬래시를 안전하게 이스케이프."""
    if text is None:
        return ""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _build_claude_command(instance: Instance) -> str:
    """단일 인스턴스에 대한 claude 실행 명령 문자열을 생성한다."""
    parts: List[str] = ["claude"]
    if instance.model:
        parts.append(f'--model "{_shell_escape_double_quotes(instance.model)}"')
    if instance.system_prompt:
        parts.append(
            f'--append-system-prompt "{_shell_escape_double_quotes(instance.system_prompt)}"'
        )
    if instance.initial_prompt:
        parts.append(f'"{_shell_escape_double_quotes(instance.initial_prompt)}"')
    return " ".join(parts)


# ----------------------------------------------------------- 일괄 실행/종료
def launch_all(
    instances: List[Instance],
    working_directory: str,
    layout_mode: str = "tabs",
    window_state: str = "normal",
) -> List[LaunchResult]:
    """enabled=True인 인스턴스들을 모두 같은 작업 디렉토리에서 실행."""
    if not working_directory or not os.path.isdir(working_directory):
        return [LaunchResult(
            "(전체)", False, f"작업 디렉토리가 존재하지 않음: {working_directory!r}",
        )]
    if not is_claude_cli_available():
        return [LaunchResult(
            "(전체)", False,
            "claude CLI를 찾을 수 없습니다. 'npm install -g @anthropic-ai/claude-code'로 먼저 설치해주세요.",
        )]

    targets = [i for i in instances if i.enabled]
    if not targets:
        return []

    system = platform.system()
    if system == "Windows":
        return _launch_windows_all(targets, working_directory, layout_mode, window_state)

    # macOS/Linux는 인스턴스마다 새 터미널을 따로 띄우는 단순 방식
    return [_launch_single_unix(inst, working_directory, system) for inst in targets]


# =========================================================== Windows 일괄 실행
def _launch_windows_all(
    instances: List[Instance],
    working_directory: str,
    layout_mode: str,
    window_state: str,
) -> List[LaunchResult]:
    """Windows Terminal(wt)이 있으면 단일 명령으로, 없으면 cmd 창을 따로 띄운다."""
    if shutil.which("wt") is None:
        # wt 미설치: 별창 모드만 가능. 사용자가 분할을 선택했어도 모두 별창.
        results: List[LaunchResult] = []
        for inst in instances:
            results.append(_launch_single_classic_cmd(inst, working_directory))
        return results

    # 별창 모드: 인스턴스마다 wt를 별도 호출하여 새 창을 만든다.
    if layout_mode == "separate":
        results = []
        for inst in instances:
            try:
                _spawn_wt_new_window([inst], working_directory, "tabs", window_state)
                results.append(LaunchResult(inst.name, True, "별도 창에서 실행됨 (wt)"))
            except Exception as e:  # pragma: no cover
                results.append(LaunchResult(inst.name, False, f"실행 실패: {e}"))
        return results

    # 탭/분할 모드: 한 번의 wt 호출로 모든 인스턴스를 한 창에 묶는다.
    try:
        _spawn_wt_new_window(instances, working_directory, layout_mode, window_state)
    except Exception as e:  # pragma: no cover
        return [LaunchResult(i.name, False, f"실행 실패: {e}") for i in instances]

    layout_label = {
        "tabs": "탭",
        "split_vertical": "세로 분할",
        "split_horizontal": "가로 분할",
    }.get(layout_mode, layout_mode)
    return [
        LaunchResult(inst.name, True, f"실행됨 ({layout_label})") for inst in instances
    ]


def _spawn_wt_new_window(
    instances: List[Instance],
    working_directory: str,
    layout_mode: str,
    window_state: str,
) -> None:
    """wt 명령을 조립해 새 창에서 인스턴스들을 띄운다.

    wt 명령행 문법 요약:
        wt [global-opts] sub-command [opts] [; sub-command [opts] ...]
    여기서 ';' 는 별도의 인자로 전달해야 sub-command 구분자로 인식된다.

    Args:
        instances: 실행할 인스턴스 리스트 (1개 이상)
        working_directory: 모든 패널/탭의 시작 디렉토리
        layout_mode: 'tabs' | 'split_vertical' | 'split_horizontal'
        window_state: 'normal' | 'maximized' | 'fullscreen'
    """
    if not instances:
        return

    args: List[str] = ["wt"]
    # 새 창 강제 (-w new): 기존 wt 창에 합쳐지지 않게 한다.
    args += ["-w", "new"]
    if window_state == "maximized":
        args.append("--maximized")
    elif window_state == "fullscreen":
        args.append("--fullscreen")

    n = len(instances)
    for idx, inst in enumerate(instances):
        if idx > 0:
            args.append(";")  # 서브커맨드 구분자

        title = inst.name.replace('"', "'") or f"claude-{idx+1}"
        claude_cmd = _build_claude_command(inst)

        if idx == 0:
            sub = ["new-tab"]
        elif layout_mode == "tabs":
            sub = ["new-tab"]
        elif layout_mode in ("split_vertical", "split_horizontal"):
            # split-pane -V/-H 는 현재(=직전 분할로 새로 만든) 패널을 분할한다.
            # 기본 -s 0.5로 연속 분할하면 첫 패널이 50%를 유지해 50/25/25... 가 된다.
            # i번째 분할(i=idx, 1..N-1) 직전 활성 패널 폭은 (N-i+1)/N 이므로,
            # 새 패널이 (N-i)/N 을 차지하도록 -s = (N-i)/(N-i+1) 을 주면
            # 모든 패널이 정확히 1/N 폭으로 균등 분할된다.
            direction = "-V" if layout_mode == "split_vertical" else "-H"
            ratio = (n - idx) / (n - idx + 1)
            sub = ["split-pane", direction, "-s", f"{ratio:.4f}"]
        else:
            sub = ["new-tab"]  # 알 수 없는 값은 안전하게 탭 모드로

        sub += ["--title", title, "-d", working_directory, "cmd", "/k", claude_cmd]
        args += sub

    # shell=False로 직접 실행 — ';' 가 셸이 아닌 wt에 의해 해석된다.
    subprocess.Popen(args, shell=False)


def _launch_single_classic_cmd(instance: Instance, working_directory: str) -> LaunchResult:
    """wt가 없을 때의 폴백: start cmd /k로 새 창을 띄운다."""
    safe_title = instance.name.replace('"', "'") or "claude"
    claude_cmd = _build_claude_command(instance)
    inner = f'cd /d "{working_directory}" && {claude_cmd}'
    try:
        subprocess.Popen(
            f'start "{safe_title}" cmd /k "{inner}"',
            shell=True,
        )
        return LaunchResult(instance.name, True, "새 cmd 창에서 실행됨 (wt 미설치 폴백)")
    except Exception as e:  # pragma: no cover
        return LaunchResult(instance.name, False, f"실행 실패: {e}")


# =========================================================== macOS / Linux
def _launch_single_unix(instance: Instance, working_directory: str, system: str) -> LaunchResult:
    """macOS / Linux 단일 인스턴스 실행."""
    claude_cmd = _build_claude_command(instance)
    try:
        if system == "Darwin":
            full = f'cd "{working_directory}" && {claude_cmd}'
            apple_safe = full.replace("\\", "\\\\").replace('"', '\\"')
            script = f'tell application "Terminal" to do script "{apple_safe}"'
            subprocess.Popen(["osascript", "-e", script])
        elif system == "Linux":
            inner = f'cd "{working_directory}" && {claude_cmd}; exec bash'
            if shutil.which("gnome-terminal") is not None:
                subprocess.Popen([
                    "gnome-terminal", "--title", instance.name, "--", "bash", "-c", inner,
                ])
            elif shutil.which("xterm") is not None:
                subprocess.Popen(["xterm", "-T", instance.name, "-e", "bash", "-c", inner])
            elif shutil.which("konsole") is not None:
                subprocess.Popen([
                    "konsole", "-p", f"tabtitle={instance.name}", "-e", "bash", "-c", inner,
                ])
            else:
                return LaunchResult(
                    instance.name, False,
                    "사용 가능한 터미널을 찾을 수 없습니다 (gnome-terminal/xterm/konsole).",
                )
        else:
            return LaunchResult(instance.name, False, f"지원하지 않는 OS: {system}")
    except FileNotFoundError as e:
        return LaunchResult(instance.name, False, f"터미널을 찾을 수 없음: {e}")
    except Exception as e:  # pragma: no cover
        return LaunchResult(instance.name, False, f"예외 발생: {e}")
    return LaunchResult(instance.name, True, "새 터미널에서 실행됨")


# -------------------------------------------------------------------- 종료
def terminate_all() -> Tuple[bool, str]:
    """현재 OS에서 실행 중인 모든 claude 프로세스를 종료한다."""
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.run(
                ["taskkill", "/F", "/T", "/IM", "claude.exe"],
                capture_output=True, text=True,
            )
            subprocess.run(
                ["taskkill", "/F", "/T", "/FI", "WINDOWTITLE eq claude*"],
                capture_output=True, text=True,
            )
            return True, result.stdout or result.stderr or "종료 시도 완료"
        else:
            subprocess.run(
                ["pkill", "-f", "claude"],
                capture_output=True, text=True,
            )
            return True, "종료 시도 완료 (pkill -f claude)"
    except FileNotFoundError:
        return False, "종료 명령(taskkill/pkill)을 찾을 수 없습니다."
    except Exception as e:  # pragma: no cover
        return False, f"종료 중 예외: {e}"
