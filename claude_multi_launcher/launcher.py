"""Claude Code CLI를 새 터미널 창에서 실행하는 OS별 로직.

작업 디렉토리는 앱 전역값을 외부에서 주입받아 사용한다(인스턴스에 보관하지 않음).

핵심 함수:
- is_claude_cli_available(): claude CLI가 PATH에 있는지 검사
- launch_instance(instance, working_directory)
- launch_all(instances, working_directory)
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
    """단일 인스턴스 실행 결과."""

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


# ------------------------------------------------------------- 단일 인스턴스 실행
def launch_instance(instance: Instance, working_directory: str) -> LaunchResult:
    """OS를 감지하여 새 터미널 창에서 claude를 실행한다.

    Args:
        instance: 실행할 인스턴스(이름/역할/프롬프트/모델만 사용)
        working_directory: 모든 인스턴스가 공유하는 전역 작업 디렉토리
    """
    if not working_directory or not os.path.isdir(working_directory):
        return LaunchResult(
            instance.name,
            False,
            f"작업 디렉토리가 존재하지 않음: {working_directory!r}",
        )

    if not is_claude_cli_available():
        return LaunchResult(
            instance.name,
            False,
            "claude CLI를 찾을 수 없습니다. 'npm install -g @anthropic-ai/claude-code'로 먼저 설치해주세요.",
        )

    system = platform.system()
    claude_cmd = _build_claude_command(instance)

    try:
        if system == "Windows":
            _launch_windows(working_directory, claude_cmd, instance.name)
        elif system == "Darwin":
            _launch_macos(working_directory, claude_cmd, instance.name)
        elif system == "Linux":
            _launch_linux(working_directory, claude_cmd, instance.name)
        else:
            return LaunchResult(
                instance.name, False, f"지원하지 않는 OS: {system}"
            )
    except FileNotFoundError as e:
        return LaunchResult(
            instance.name,
            False,
            f"터미널 실행 파일을 찾을 수 없습니다: {e}",
        )
    except Exception as e:  # pragma: no cover
        return LaunchResult(instance.name, False, f"예외 발생: {e}")

    return LaunchResult(instance.name, True, "새 터미널에서 실행됨")


# ------------------------------------------------------------------- Windows
def _launch_windows(work_dir: str, claude_cmd: str, title: str) -> None:
    """Windows Terminal(wt) 우선, 없으면 cmd로 새 창을 띄운다."""
    safe_title = title.replace('"', "'")
    inner_cmd = f'cd /d "{work_dir}" && {claude_cmd}'

    if shutil.which("wt") is not None:
        subprocess.Popen(
            [
                "wt", "new-tab",
                "--title", safe_title,
                "-d", work_dir,
                "cmd", "/k", claude_cmd,
            ],
            shell=False,
        )
    else:
        subprocess.Popen(
            f'start "{safe_title}" cmd /k "{inner_cmd}"',
            shell=True,
        )


# ---------------------------------------------------------------------- macOS
def _launch_macos(work_dir: str, claude_cmd: str, title: str) -> None:
    """osascript로 Terminal.app에 새 창을 열고 명령을 입력시킨다."""
    full = f'cd "{work_dir}" && {claude_cmd}'
    apple_safe = full.replace("\\", "\\\\").replace('"', '\\"')
    script = f'tell application "Terminal" to do script "{apple_safe}"'
    subprocess.Popen(["osascript", "-e", script])


# ---------------------------------------------------------------------- Linux
def _launch_linux(work_dir: str, claude_cmd: str, title: str) -> None:
    """gnome-terminal → xterm → konsole 순으로 시도."""
    inner = f'cd "{work_dir}" && {claude_cmd}; exec bash'

    if shutil.which("gnome-terminal") is not None:
        subprocess.Popen([
            "gnome-terminal", "--title", title, "--", "bash", "-c", inner,
        ])
    elif shutil.which("xterm") is not None:
        subprocess.Popen(["xterm", "-T", title, "-e", "bash", "-c", inner])
    elif shutil.which("konsole") is not None:
        subprocess.Popen(["konsole", "-p", f"tabtitle={title}", "-e", "bash", "-c", inner])
    else:
        raise FileNotFoundError(
            "사용 가능한 터미널을 찾을 수 없습니다 (gnome-terminal, xterm, konsole)."
        )


# ----------------------------------------------------------- 일괄 실행/종료
def launch_all(instances: List[Instance], working_directory: str) -> List[LaunchResult]:
    """enabled=True인 인스턴스들을 모두 같은 작업 디렉토리에서 실행."""
    results: List[LaunchResult] = []
    for inst in instances:
        if not inst.enabled:
            continue
        results.append(launch_instance(inst, working_directory))
    return results


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
