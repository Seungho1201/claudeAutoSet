"""설정 파일(config.json) 입출력 및 인스턴스 데이터 모델.

- Instance: 단일 인스턴스를 표현하는 dataclass (작업 디렉토리는 포함하지 않음)
- ConfigManager: 전역 작업 디렉토리 + 인스턴스 리스트의 영속화

config.json 스키마:
    {
        "working_directory": "C:/path/to/project",
        "layout_mode": "tabs" | "split_vertical" | "split_horizontal" | "separate",
        "window_state": "normal" | "maximized" | "fullscreen",
        "language": "ko" | "en" | "ja",
        "instances": [ {name, role, system_prompt, initial_prompt, model, enabled}, ... ]
    }
"""

from __future__ import annotations

import copy
import json
import os
from dataclasses import asdict, dataclass
from typing import List, Optional


# 레이아웃/창 상태/언어 허용값 (validation용)
LAYOUT_MODES = ("tabs", "split_vertical", "split_horizontal", "separate")
WINDOW_STATES = ("normal", "maximized", "fullscreen")
LANGUAGES = ("ko", "en", "ja")


@dataclass
class Instance:
    """Claude Code 인스턴스 한 개를 나타내는 데이터 모델.

    작업 디렉토리는 ConfigManager 레벨에서 전역으로 관리하므로 여기에 두지 않는다.
    """

    name: str = ""
    role: str = ""
    system_prompt: str = ""
    initial_prompt: str = ""
    model: str = ""           # 빈 문자열이면 Claude CLI 기본값 사용
    enabled: bool = True

    def to_dict(self) -> dict:
        """JSON 직렬화를 위한 dict 변환."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Instance":
        """dict에서 Instance 생성. 알려진 필드만 복원해 구버전과 호환."""
        known = {"name", "role", "system_prompt", "initial_prompt", "model", "enabled"}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class ConfigManager:
    """config.json의 로드/저장과 전역 작업 폴더 + 인스턴스 컬렉션 관리."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """ConfigManager 초기화.

        Args:
            config_path: 설정 파일 경로. None이면 이 모듈과 같은 디렉토리의 config.json 사용.
        """
        if config_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "config.json")
        self.config_path: str = config_path
        self.working_directory: str = ""
        self.layout_mode: str = "tabs"
        self.window_state: str = "normal"
        self.language: str = "ko"
        self.instances: List[Instance] = []

    # ---------------------------------------------------------------- I/O
    def load(self) -> List[Instance]:
        """설정 파일에서 전역 작업 폴더 + 인스턴스 목록을 읽어들인다.

        구버전(인스턴스마다 working_directory가 있는 형식)도 자동으로 마이그레이션한다.
        - 전역 working_directory 키가 없으면, 인스턴스들의 working_directory 중
          가장 먼저 발견되는 비어있지 않은 값을 전역값으로 채택한다.
        """
        if not os.path.exists(self.config_path):
            self.working_directory = ""
            self.layout_mode = "tabs"
            self.window_state = "normal"
            self.language = "ko"
            self.instances = []
            return self.instances

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"설정 파일이 손상되었습니다: {self.config_path}\n{e}"
            ) from e

        if not isinstance(data, dict):
            data = {}

        # 인스턴스 복원 (구버전 working_directory 필드는 from_dict가 무시함)
        raw_list = data.get("instances", [])
        self.instances = [Instance.from_dict(item) for item in raw_list]

        # 레이아웃/창 상태 (없으면 기본값 유지)
        layout = data.get("layout_mode")
        if isinstance(layout, str) and layout in LAYOUT_MODES:
            self.layout_mode = layout
        else:
            self.layout_mode = "tabs"

        wstate = data.get("window_state")
        if isinstance(wstate, str) and wstate in WINDOW_STATES:
            self.window_state = wstate
        else:
            self.window_state = "normal"

        # 언어 (없거나 잘못된 값이면 기본값 'ko')
        lang = data.get("language")
        if isinstance(lang, str) and lang in LANGUAGES:
            self.language = lang
        else:
            self.language = "ko"

        # 전역 작업 폴더 결정
        wd = data.get("working_directory")
        if isinstance(wd, str) and wd.strip():
            self.working_directory = wd.strip()
        else:
            # 구버전 마이그레이션: 인스턴스에 들어있던 첫 working_directory를 전역값으로
            migrated = ""
            for item in raw_list:
                v = item.get("working_directory") if isinstance(item, dict) else None
                if isinstance(v, str) and v.strip():
                    migrated = v.strip()
                    break
            self.working_directory = migrated
            # 마이그레이션이 일어났다면 새 포맷으로 즉시 저장
            if migrated:
                self.save()

        return self.instances

    def save(self) -> None:
        """현재 상태(전역 작업 폴더 + 인스턴스들)를 config.json에 저장."""
        payload = {
            "working_directory": self.working_directory,
            "layout_mode": self.layout_mode,
            "window_state": self.window_state,
            "language": self.language,
            "instances": [inst.to_dict() for inst in self.instances],
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # ---------------------------------------------------- 전역 작업 폴더 API
    def set_working_directory(self, path: str) -> None:
        """전역 작업 디렉토리를 설정하고 즉시 저장한다."""
        self.working_directory = (path or "").strip()
        self.save()

    def set_layout_mode(self, mode: str) -> None:
        """레이아웃 모드를 설정하고 즉시 저장."""
        if mode not in LAYOUT_MODES:
            raise ValueError(f"알 수 없는 layout_mode: {mode}")
        self.layout_mode = mode
        self.save()

    def set_window_state(self, state: str) -> None:
        """창 상태(normal/maximized/fullscreen)를 설정하고 즉시 저장."""
        if state not in WINDOW_STATES:
            raise ValueError(f"알 수 없는 window_state: {state}")
        self.window_state = state
        self.save()

    def set_language(self, lang: str) -> None:
        """UI 언어(ko/en/ja)를 설정하고 즉시 저장."""
        if lang not in LANGUAGES:
            raise ValueError(f"알 수 없는 language: {lang}")
        self.language = lang
        self.save()

    # ----------------------------------------------------------- CRUD API
    def add(self, instance: Instance) -> None:
        """새 인스턴스를 추가하고 즉시 저장."""
        self.instances.append(instance)
        self.save()

    def update(self, index: int, instance: Instance) -> None:
        """인덱스 위치의 인스턴스를 교체하고 즉시 저장."""
        if not 0 <= index < len(self.instances):
            raise IndexError(f"잘못된 인스턴스 인덱스: {index}")
        self.instances[index] = instance
        self.save()

    def delete(self, index: int) -> None:
        """인덱스 위치의 인스턴스를 제거하고 즉시 저장."""
        if not 0 <= index < len(self.instances):
            raise IndexError(f"잘못된 인스턴스 인덱스: {index}")
        del self.instances[index]
        self.save()

    def duplicate(self, index: int) -> Instance:
        """인스턴스를 복제하여 바로 뒤에 삽입. 이름 뒤에 현재 언어의 '복사' 접미사 부여."""
        if not 0 <= index < len(self.instances):
            raise IndexError(f"잘못된 인스턴스 인덱스: {index}")
        from i18n import t  # 순환 import 회피용 지연 import
        original = self.instances[index]
        copied = copy.deepcopy(original)
        copied.name = f"{original.name}{t('copy_suffix')}"
        self.instances.insert(index + 1, copied)
        self.save()
        return copied

    def toggle_enabled(self, index: int) -> bool:
        """활성/비활성 토글. 변경된 enabled 값을 반환."""
        if not 0 <= index < len(self.instances):
            raise IndexError(f"잘못된 인스턴스 인덱스: {index}")
        self.instances[index].enabled = not self.instances[index].enabled
        self.save()
        return self.instances[index].enabled

    # ------------------------------------------------------------- 샘플 시드
    def ensure_sample_data(self) -> bool:
        """설정 파일이 비어 있으면 샘플 인스턴스 3개를 추가한다.

        Returns:
            샘플 데이터를 새로 생성했으면 True, 기존 데이터가 있으면 False.
        """
        if self.instances:
            return False

        if not self.working_directory:
            self.working_directory = os.path.expanduser("~")

        samples = [
            Instance(
                name="프론트엔드 담당",
                role="React 개발자",
                system_prompt="당신은 React/TypeScript 전문가입니다. 컴포넌트 분리와 접근성을 중시하세요.",
                initial_prompt="현재 프로젝트의 컴포넌트 구조를 살펴보고 개선점을 정리해주세요.",
                model="",
                enabled=True,
            ),
            Instance(
                name="백엔드 담당",
                role="Python 백엔드 개발자",
                system_prompt="당신은 FastAPI 및 SQL 데이터베이스 전문가입니다. 보안과 성능을 우선시하세요.",
                initial_prompt="API 엔드포인트 목록을 정리하고 개선이 필요한 부분을 찾아주세요.",
                model="",
                enabled=True,
            ),
            Instance(
                name="문서화 담당",
                role="Technical Writer",
                system_prompt="당신은 명확하고 간결한 기술 문서를 작성하는 전문가입니다.",
                initial_prompt="README.md를 검토하고 부족한 섹션을 보강해주세요.",
                model="",
                enabled=False,
            ),
        ]
        self.instances.extend(samples)
        self.save()
        return True
