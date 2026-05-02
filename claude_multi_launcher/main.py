"""Claude Code Multi Launcher - 메인 GUI.

여러 Claude Code 인스턴스를 한 번의 클릭으로 동시 실행하기 위한 customtkinter
기반 데스크톱 앱.

기능 요약:
- 인스턴스 목록 (활성/비활성 체크박스)
- 작업시작 / 인스턴스 추가/수정/삭제 / 전체 종료 버튼
- 더블클릭 → 수정, 우클릭 → 컨텍스트 메뉴(복제/삭제/활성화 토글)
- 하단 실행 로그 영역
- ⚙ 설정 버튼 → 하단 인라인 패널에서 언어 선택(한국어/English/日本語) — 즉시 반영
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox
from typing import List, Optional

import customtkinter as ctk

# PIL은 customtkinter의 CTkImage 사용에 필요. 설치 안 된 환경에서는 텍스트 폴백.
try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:
    Image = None  # type: ignore[assignment]
    _HAS_PIL = False

from config_manager import ConfigManager, Instance
from i18n import (
    LANGUAGE_DISPLAY_NAMES,
    SUPPORTED_LANGUAGES,
    current_language,
    set_language,
    t,
)
from instance_dialog import InstanceDialog
from launcher import (
    LaunchResult,
    is_claude_cli_available,
    launch_all,
    terminate_all,
)


# 외관 기본값
ctk.set_appearance_mode("System")     # "Light" / "Dark" / "System"
ctk.set_default_color_theme("blue")


# 클로드 마스코트 아이콘 (PNG)
_ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon")
CLAUDE_ICON_PATH = os.path.join(_ICON_DIR, "icons8-클로드-96.png")

# 격자 카드 레이아웃 상수
CARD_SIZE = 140          # 카드 기본 가로 폭 (px) — 셀에 맞춰 가로로 늘어남
CARD_HEIGHT = 300        # 카드 세로 높이 고정 (px) — viewport 동적 계산은 무한 증식 위험으로 제거
CARD_ICON_SIZE = 60      # 카드 안 클로드 아이콘 표시 크기 (px)
CARD_GAP = 4             # 카드 간 여백 (grid padx/pady, px)
MAX_GRID_COLUMNS = 4     # 한 줄에 들어갈 수 있는 최대 카드 수 (이보다 많으면 다음 줄로)


class InstanceCard(ctk.CTkFrame):
    """디스코드 스타일의 정사각형 카드 — 인스턴스 한 개를 표시.

    레이아웃 (140x140):
        ┌──────────┐
        │ ☑        │  좌상단: 활성화 체크박스
        │   🟠     │  중앙 상단: 클로드 마스코트 PNG (60x60)
        │  이름     │  하단: 사용자가 지정한 이름만
        └──────────┘
    """

    # 클로드 마스코트 CTkImage — 첫 카드 생성 시 1회 로드, 이후 재사용
    _icon_image: Optional[ctk.CTkImage] = None
    # 이미지 로드 실패 시 True로 잠겨 텍스트 폴백 사용
    _icon_load_failed: bool = False

    @classmethod
    def _ensure_icon_loaded(cls) -> Optional[ctk.CTkImage]:
        """클로드 PNG 아이콘을 lazy-load 하여 캐시. PIL 부재/파일 부재/오류 시 None."""
        if cls._icon_image is not None or cls._icon_load_failed:
            return cls._icon_image
        if not _HAS_PIL:
            cls._icon_load_failed = True
            return None
        try:
            pil_img = Image.open(CLAUDE_ICON_PATH)
            cls._icon_image = ctk.CTkImage(
                light_image=pil_img, dark_image=pil_img,
                size=(CARD_ICON_SIZE, CARD_ICON_SIZE),
            )
        except Exception:
            cls._icon_load_failed = True
            cls._icon_image = None
        return cls._icon_image

    def __init__(
        self,
        master,
        index: int,
        instance: Instance,
        on_toggle,            # callable(index, bool)
        on_double_click,      # callable(index)
        on_right_click,       # callable(index, x, y)
    ) -> None:
        super().__init__(
            master, corner_radius=12,
            width=CARD_SIZE, height=CARD_HEIGHT,
            fg_color=("gray92", "gray18"),
        )
        # 카드 사이즈 고정 — 자식들의 크기에 따라 변형되지 않게
        self.grid_propagate(False)
        self.pack_propagate(False)
        self.index = index
        self.instance = instance

        # 좌상단 체크박스 (카드 전체 기준 절대 위치)
        self.enabled_var = ctk.BooleanVar(value=instance.enabled)
        self.check = ctk.CTkCheckBox(
            self, text="", width=20, variable=self.enabled_var,
            command=lambda: on_toggle(self.index, bool(self.enabled_var.get())),
        )
        self.check.place(x=8, y=8)

        # 콘텐츠 inner frame — 카드가 가로/세로로 늘어나도 아이콘+이름이
        # 가운데에 응집되도록 별도 컨테이너에 묶고 anchor="center"로 위치.
        self._inner = ctk.CTkFrame(self, fg_color="transparent")
        self._inner.place(relx=0.5, rely=0.5, anchor="center")

        # 클로드 마스코트 PNG (실패 시 텍스트 폴백)
        icon_img = self._ensure_icon_loaded()
        if icon_img is not None:
            self.icon_label = ctk.CTkLabel(self._inner, image=icon_img, text="")
        else:
            self.icon_label = ctk.CTkLabel(
                self._inner, text="C",
                font=ctk.CTkFont(size=26, weight="bold"),
                text_color=("#d97757", "#e89272"),
            )
        self.icon_label.pack(pady=(0, 8))

        # 사용자가 지정한 이름만 표시
        name_text = instance.name if instance.name else t("list.unnamed")
        self.name_label = ctk.CTkLabel(
            self._inner, text=name_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            wraplength=CARD_SIZE * 2,  # 카드가 가로로 늘어날 수 있으므로 여유롭게
        )
        self.name_label.pack()
        # role_label 자리표시 (이전 코드와의 호환성 — _refresh_list에서 None 체크)
        self.role_label = None

        # 이벤트 바인딩 — 카드와 inner / 표시 자식 모두에
        for w in (self, self._inner, self.icon_label, self.name_label):
            w.bind("<Double-Button-1>", lambda e: on_double_click(self.index))
            w.bind("<Button-3>", lambda e: on_right_click(self.index, e.x_root, e.y_root))


class App(ctk.CTk):
    """메인 애플리케이션 윈도우."""

    def __init__(self) -> None:
        super().__init__()
        # 시작 크기를 minsize와 동일하게 — 사용자가 가장 작은 사이즈로 시작 요청
        self.geometry("960x720")
        self.minsize(960, 720)

        # 설정 로드
        self.config_manager = ConfigManager()
        try:
            self.config_manager.load()
        except RuntimeError as e:
            # 아직 i18n이 적용되기 전이지만 한국어 기본 fallback
            messagebox.showerror(t("msg.config_error_title"), str(e))
            self.config_manager.instances = []

        # 비어 있으면 샘플 시드
        self.config_manager.ensure_sample_data()

        # 저장된 언어를 i18n에 적용
        set_language(self.config_manager.language)

        # 메인 창 제목 (언어 적용 후)
        self.title(t("app.title"))

        # 상태 변수
        self._selected_index: Optional[int] = None
        self._context_index: Optional[int] = None
        self.row_widgets: List[ctk.CTkBaseClass] = []
        # 하단 설정 패널 토글 상태 (언어 변경 시 보존)
        self._settings_panel_open = False
        # 실행 로그 펼침 상태 (기본 접힘)
        self._log_open = False
        # 누적 로그 라인 (언어 재구성 시 보존)
        self._log_buffer: List[str] = []

        self._build_ui()
        self._refresh_list()

        # 시작 시 claude CLI 존재 여부 점검
        if not is_claude_cli_available():
            self._log(t("log.cli_missing"), level="warn")

    # ----------------------------------------------------------------- UI 구성
    def _build_ui(self) -> None:
        """전체 레이아웃 구성. 언어 변경 시 _rebuild_ui에서 재호출 가능."""
        # ---- 상단 헤더
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray85", "gray20"))
        header.pack(fill="x", side="top")

        title = ctk.CTkLabel(
            header, text=t("app.title"),
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(side="left", padx=20, pady=14)

        subtitle = ctk.CTkLabel(
            header, text=t("app.subtitle"),
            text_color=("gray30", "gray70"),
        )
        subtitle.pack(side="left", padx=(0, 20), pady=14)

        # 헤더 우측: 설정 버튼
        ctk.CTkButton(
            header, text=t("app.settings_button"), width=110,
            fg_color=("gray70", "gray30"), hover_color=("gray60", "gray35"),
            command=self._toggle_settings_panel,
        ).pack(side="right", padx=16, pady=14)

        # ---- 전역 작업 폴더 바 (모든 인스턴스 공통)
        workdir_bar = ctk.CTkFrame(self, corner_radius=8)
        workdir_bar.pack(fill="x", padx=16, pady=(12, 0))
        workdir_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            workdir_bar, text=t("workdir.label"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")

        self.workdir_entry = ctk.CTkEntry(
            workdir_bar, placeholder_text=t("workdir.placeholder"),
        )
        self.workdir_entry.grid(row=0, column=1, padx=(0, 8), pady=10, sticky="ew")
        self.workdir_entry.insert(0, self.config_manager.working_directory or "")
        self.workdir_entry.bind("<FocusOut>", lambda e: self._save_workdir_from_entry())
        self.workdir_entry.bind("<Return>", lambda e: self._save_workdir_from_entry())

        ctk.CTkButton(
            workdir_bar, text=t("workdir.browse"), width=110,
            command=self._browse_workdir,
        ).grid(row=0, column=2, padx=(0, 12), pady=10)

        # ---- 레이아웃 / 창 상태 옵션 바 (Windows Terminal 한정)
        layout_bar = ctk.CTkFrame(self, corner_radius=8)
        layout_bar.pack(fill="x", padx=16, pady=(8, 0))

        ctk.CTkLabel(
            layout_bar, text=t("layout.label"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")

        # 표시용(현재 언어) ↔ 내부 키 매핑
        self._layout_display_to_key = {
            t("layout.tabs"): "tabs",
            t("layout.split_vertical"): "split_vertical",
            t("layout.split_horizontal"): "split_horizontal",
            t("layout.separate"): "separate",
        }
        self._layout_key_to_display = {v: k for k, v in self._layout_display_to_key.items()}

        self.layout_menu = ctk.CTkOptionMenu(
            layout_bar,
            values=list(self._layout_display_to_key.keys()),
            width=200,
            command=self._on_layout_change,
        )
        self.layout_menu.set(
            self._layout_key_to_display.get(self.config_manager.layout_mode, t("layout.tabs"))
        )
        self.layout_menu.grid(row=0, column=1, padx=(0, 16), pady=10, sticky="w")

        ctk.CTkLabel(
            layout_bar, text=t("wstate.label"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=2, padx=(0, 8), pady=10, sticky="w")

        self._wstate_display_to_key = {
            t("wstate.normal"): "normal",
            t("wstate.maximized"): "maximized",
            t("wstate.fullscreen"): "fullscreen",
        }
        self._wstate_key_to_display = {v: k for k, v in self._wstate_display_to_key.items()}

        self.wstate_menu = ctk.CTkOptionMenu(
            layout_bar,
            values=list(self._wstate_display_to_key.keys()),
            width=130,
            command=self._on_wstate_change,
        )
        self.wstate_menu.set(
            self._wstate_key_to_display.get(self.config_manager.window_state, t("wstate.normal"))
        )
        self.wstate_menu.grid(row=0, column=3, padx=(0, 12), pady=10, sticky="w")

        # 우측 안내
        ctk.CTkLabel(
            layout_bar,
            text=t("layout.note"),
            text_color=("gray35", "gray65"), font=ctk.CTkFont(size=11),
        ).grid(row=0, column=4, padx=(0, 12), pady=10, sticky="e")
        layout_bar.grid_columnconfigure(4, weight=1)

        # ---- 큰 작업시작 버튼 + 보조 버튼들
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=16, pady=(12, 0))

        self.start_btn = ctk.CTkButton(
            action_bar, text=t("action.start"),
            height=52, font=ctk.CTkFont(size=16, weight="bold"),
            command=self._on_start,
        )
        self.start_btn.pack(side="left", fill="x", expand=True)

        self.terminate_btn = ctk.CTkButton(
            action_bar, text=t("action.terminate"), height=52, width=140,
            fg_color="#a83232", hover_color="#7a2424",
            command=self._on_terminate_all,
        )
        self.terminate_btn.pack(side="left", padx=(8, 0))

        # ---- CRUD 버튼
        crud_bar = ctk.CTkFrame(self, fg_color="transparent")
        crud_bar.pack(fill="x", padx=16, pady=(8, 0))
        ctk.CTkButton(crud_bar, text=t("crud.add"), width=160,
                      command=self._on_add).pack(side="left")
        ctk.CTkButton(crud_bar, text=t("crud.edit"), width=110,
                      command=self._on_edit_selected).pack(side="left", padx=(8, 0))
        ctk.CTkButton(crud_bar, text=t("crud.delete"), width=110,
                      fg_color="gray40", hover_color="gray30",
                      command=self._on_delete_selected).pack(side="left", padx=(8, 0))

        hint = ctk.CTkLabel(
            crud_bar,
            text=t("crud.hint"),
            text_color=("gray35", "gray65"), font=ctk.CTkFont(size=11),
        )
        hint.pack(side="right", padx=(8, 0))

        # ---- 인스턴스 리스트 (스크롤)
        list_label = ctk.CTkLabel(
            self, text=t("list.title"),
            anchor="w", font=ctk.CTkFont(size=13, weight="bold"),
        )
        list_label.pack(fill="x", padx=18, pady=(14, 4))

        self.list_frame = ctk.CTkScrollableFrame(self, height=320)
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        # ---- 로그 영역 (헤더 + 본문) — 기본 접힘
        log_header = ctk.CTkFrame(self, fg_color="transparent")
        log_header.pack(fill="x", padx=18, pady=(8, 4))

        ctk.CTkLabel(
            log_header, text=t("log.title"),
            anchor="w", font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")

        # 펼침/접힘 토글 버튼 — 접혀 있을 땐 ▼, 펼쳐졌을 땐 ▲
        self.log_toggle_btn = ctk.CTkButton(
            log_header,
            text="▲" if self._log_open else "▼",
            width=32, height=24,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            text_color=("gray20", "gray80"),
            command=self._toggle_log,
        )
        self.log_toggle_btn.pack(side="right")

        self.log_text = ctk.CTkTextbox(self, height=160, wrap="word")
        # 누적 로그 복원 — pack 여부와 무관하게 미리 채워둠 (펼치면 바로 보임)
        if self._log_buffer:
            for line in self._log_buffer:
                self.log_text.insert("end", line)
            self.log_text.see("end")
        self.log_text.configure(state="disabled")
        # 펼침 상태일 때만 화면에 pack
        if self._log_open:
            self.log_text.pack(fill="both", expand=False, padx=16, pady=(0, 16))

        # ---- 하단 설정 패널 (초기 hidden, 토글로 등장)
        # 핵심: list_frame(expand=True)이 모든 잉여 공간을 빨아가서 settings_panel
        # 자체 높이가 0px로 계산되는 문제가 있다. 명시적 height + pack_propagate(False)
        # 로 자식 크기 전파를 막고 고정 높이를 강제한다.
        self.settings_panel = ctk.CTkFrame(
            self, corner_radius=8, fg_color=("gray90", "gray22"), height=72,
        )
        self.settings_panel.pack_propagate(False)
        self._build_settings_panel(self.settings_panel)

        # 이전 토글 상태 복원 (언어 변경 후)
        if self._settings_panel_open:
            self.settings_panel.pack(fill="x", padx=16, pady=(0, 12))

        # ---- 우클릭 컨텍스트 메뉴 (tk.Menu 사용 — CTk엔 Menu가 없음)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label=t("ctx.edit"), command=self._ctx_edit)
        self.context_menu.add_command(label=t("ctx.duplicate"), command=self._ctx_duplicate)
        self.context_menu.add_command(label=t("ctx.toggle"), command=self._ctx_toggle)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=t("ctx.delete"), command=self._ctx_delete)

        # 행 위젯 컨테이너 초기화
        self.row_widgets = []

    # ------------------------------------------------------- 설정 패널 (하단)
    def _build_settings_panel(self, parent: ctk.CTkFrame) -> None:
        """하단 설정 패널 내부를 단일 행으로 구성한다 (고정 높이에 안정적으로 맞도록)."""
        # 좌측: 제목
        ctk.CTkLabel(
            parent, text=t("settings.title"),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(14, 16), pady=10)

        # 언어 라벨
        ctk.CTkLabel(
            parent, text=t("settings.language_label"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 12), pady=10)

        # 언어 라디오 그룹
        self._language_var = tk.StringVar(value=self.config_manager.language)
        for code in SUPPORTED_LANGUAGES:
            ctk.CTkRadioButton(
                parent,
                text=LANGUAGE_DISPLAY_NAMES[code],
                value=code,
                variable=self._language_var,
                command=self._on_language_change,
            ).pack(side="left", padx=(0, 14), pady=10)

        # 우측: 닫기 버튼
        ctk.CTkButton(
            parent, text=t("settings.close"), width=90,
            fg_color="gray40", hover_color="gray30",
            command=self._toggle_settings_panel,
        ).pack(side="right", padx=14, pady=10)

    def _toggle_settings_panel(self) -> None:
        """하단 설정 패널 토글.

        다른 위젯들이 이미 top으로 packed된 상태이므로 settings_panel도 기본 top
        흐름으로 추가한다 — 결과적으로 마지막에 위치하여 화면 하단에 표시된다.
        """
        if self._settings_panel_open:
            self.settings_panel.pack_forget()
            self._settings_panel_open = False
            self._log("⚙ settings panel closed")
        else:
            self.settings_panel.pack(fill="x", padx=16, pady=(0, 12))
            self._settings_panel_open = True
            self._log("⚙ settings panel opened")
        # 즉시 화면 갱신 — 일부 환경에서 pack 후 리렌더가 지연되는 경우 대비
        try:
            self.update_idletasks()
        except Exception:
            pass

    def _toggle_log(self) -> None:
        """실행 로그 본문 영역을 펼침/접힘 토글한다.

        본문 textbox는 항상 메모리에 존재하며 _log_buffer로 라인 누적되므로,
        펼치는 순간 그동안 쌓인 로그가 바로 표시된다.
        """
        if self._log_open:
            self.log_text.pack_forget()
            self._log_open = False
            self.log_toggle_btn.configure(text="▼")
        else:
            self.log_text.pack(fill="both", expand=False, padx=16, pady=(0, 16))
            self._log_open = True
            self.log_toggle_btn.configure(text="▲")
            try:
                self.log_text.see("end")
            except Exception:
                pass

    def _on_language_change(self) -> None:
        """언어 라디오 변경 — 즉시 i18n에 반영하고 UI 재구성."""
        new_lang = self._language_var.get()
        if new_lang == current_language():
            return
        self.config_manager.set_language(new_lang)
        set_language(new_lang)
        self._log(t("log.language_changed", language=LANGUAGE_DISPLAY_NAMES[new_lang]))
        self._rebuild_ui()

    def _rebuild_ui(self) -> None:
        """UI 전체를 현재 언어로 다시 그린다.

        모든 자식 위젯을 destroy하고 _build_ui()를 재호출한다.
        로그/선택 인덱스/설정 패널 토글 상태는 인스턴스 변수로 보존된다.
        """
        # 메인 창 자식 위젯 모두 제거
        for child in list(self.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass

        # 창 제목도 갱신
        self.title(t("app.title"))

        # UI 다시 구성
        self._build_ui()
        self._refresh_list()

    # ---------------------------------------------------------- 리스트 갱신/선택
    def _refresh_list(self) -> None:
        """ConfigManager의 인스턴스 리스트를 격자 카드 형태로 화면에 다시 그린다."""
        # 기존 위젯 제거
        for w in self.row_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self.row_widgets.clear()

        n = len(self.config_manager.instances)
        if n == 0:
            empty = ctk.CTkLabel(
                self.list_frame,
                text=t("list.empty"),
                text_color=("gray35", "gray65"),
            )
            empty.grid(row=0, column=0, columnspan=MAX_GRID_COLUMNS, pady=40, padx=20, sticky="ew")
            self.row_widgets.append(empty)
            return

        # 컬럼 수는 인스턴스 수에 맞춰 동적 결정 — 2개면 2컬럼(각 50%),
        # 3개면 3컬럼(33%), 4개면 4컬럼(25%). 5개 이상이면 MAX_GRID_COLUMNS(=4)로
        # 한 줄을 채우고 나머지는 다음 줄로 넘긴다.
        cols = max(1, min(n, MAX_GRID_COLUMNS))

        # 사용 중인 컬럼만 weight=1로 균등 분할. 사용 안 하는 컬럼은 weight=0으로 초기화.
        for c in range(MAX_GRID_COLUMNS):
            self.list_frame.grid_columnconfigure(
                c, weight=1 if c < cols else 0, uniform="card_col" if c < cols else "",
            )
        # 행 weight는 부여하지 않는다 — 카드 height를 CARD_HEIGHT(고정)으로 두고,
        # 행은 카드 높이만큼만 차지. 이전 호출 잔재만 0으로 초기화.
        for r in range(16):
            self.list_frame.grid_rowconfigure(r, weight=0)

        for i, inst in enumerate(self.config_manager.instances):
            grid_row = i // cols
            grid_col = i % cols
            card = InstanceCard(
                self.list_frame,
                index=i,
                instance=inst,
                on_toggle=self._on_row_toggle,
                on_double_click=self._on_row_double_click,
                on_right_click=self._on_row_right_click,
            )
            # sticky="ew" — 가로만 셀에 맞춰 fill (세로는 CARD_HEIGHT 고정)
            card.grid(row=grid_row, column=grid_col, padx=CARD_GAP, pady=CARD_GAP, sticky="ew")
            # 단일 클릭 → 선택. 카드와 자식 위젯들에 모두 바인딩
            click_targets = [card, card.icon_label, card.name_label]
            if card.role_label is not None:
                click_targets.append(card.role_label)
            for sub in click_targets:
                sub.bind("<Button-1>", lambda e, idx=i: self._select_row(idx))
            self.row_widgets.append(card)

        # 선택 인덱스가 범위를 벗어났으면 초기화
        if self._selected_index is not None and self._selected_index >= len(self.config_manager.instances):
            self._selected_index = None

        self._highlight_selected()

    def _select_row(self, index: int) -> None:
        """클릭으로 선택된 카드 인덱스를 갱신하고 강조."""
        self._selected_index = index
        self._highlight_selected()

    def _highlight_selected(self) -> None:
        """선택된 카드에 시각적 강조를 적용."""
        for w in self.row_widgets:
            if isinstance(w, InstanceCard):
                if self._selected_index is not None and w.index == self._selected_index:
                    w.configure(fg_color=("#cfe2ff", "#1f3a5f"))
                else:
                    w.configure(fg_color=("gray92", "gray18"))

    # ---------------------------------------------------------------- 행 이벤트
    def _on_row_toggle(self, index: int, value: bool) -> None:
        """체크박스로 enabled 토글."""
        self.config_manager.instances[index].enabled = value
        self.config_manager.save()

    def _on_row_double_click(self, index: int) -> None:
        """더블클릭 → 수정 다이얼로그."""
        self._select_row(index)
        self._edit_at(index)

    def _on_row_right_click(self, index: int, x: int, y: int) -> None:
        """우클릭 → 컨텍스트 메뉴."""
        self._select_row(index)
        self._context_index = index
        try:
            self.context_menu.tk_popup(x, y)
        finally:
            self.context_menu.grab_release()

    # -------------------------------------------------------- 컨텍스트 메뉴 핸들러
    def _ctx_edit(self) -> None:
        if self._context_index is not None:
            self._edit_at(self._context_index)

    def _ctx_duplicate(self) -> None:
        if self._context_index is None:
            return
        try:
            new_inst = self.config_manager.duplicate(self._context_index)
            self._log(t("ctx.duplicated", name=new_inst.name))
            self._refresh_list()
        except Exception as e:
            messagebox.showerror(t("msg.error_title"), t("msg.duplicate_failed", error=e))

    def _ctx_toggle(self) -> None:
        if self._context_index is None:
            return
        new_state = self.config_manager.toggle_enabled(self._context_index)
        state_label = t("ctx.toggled_on") if new_state else t("ctx.toggled_off")
        self._log(t(
            "ctx.toggle_log",
            name=self.config_manager.instances[self._context_index].name,
            state=state_label,
        ))
        self._refresh_list()

    def _ctx_delete(self) -> None:
        if self._context_index is not None:
            self._delete_at(self._context_index)

    # ---------------------------------------------------------------- CRUD 액션
    def _on_add(self) -> None:
        """'인스턴스 추가' 버튼 — 빈 다이얼로그를 띄운다."""
        dialog = InstanceDialog(self, instance=None)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.config_manager.add(dialog.result)
            self._log(t("log.added", name=dialog.result.name))
            self._refresh_list()

    def _on_edit_selected(self) -> None:
        """'수정' 버튼 — 선택된 항목을 수정."""
        if self._selected_index is None:
            messagebox.showinfo(t("msg.info_title"), t("msg.select_first_edit"))
            return
        self._edit_at(self._selected_index)

    def _edit_at(self, index: int) -> None:
        """인덱스에 해당하는 인스턴스를 수정 다이얼로그로 연다."""
        original = self.config_manager.instances[index]
        dialog = InstanceDialog(self, instance=original)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.config_manager.update(index, dialog.result)
            self._log(t("log.updated", name=dialog.result.name))
            self._refresh_list()

    def _on_delete_selected(self) -> None:
        """'삭제' 버튼 — 선택된 항목을 삭제."""
        if self._selected_index is None:
            messagebox.showinfo(t("msg.info_title"), t("msg.select_first_delete"))
            return
        self._delete_at(self._selected_index)

    def _delete_at(self, index: int) -> None:
        """확인 후 인덱스 위치의 인스턴스를 삭제한다."""
        inst = self.config_manager.instances[index]
        if not messagebox.askyesno(
            t("msg.delete_confirm_title"), t("msg.delete_confirm_body", name=inst.name),
        ):
            return
        self.config_manager.delete(index)
        self._log(t("log.deleted", name=inst.name))
        self._selected_index = None
        self._refresh_list()

    # ----------------------------------------------------------- 작업 폴더
    def _save_workdir_from_entry(self) -> None:
        """입력창의 값을 전역 작업 폴더로 저장."""
        new_value = self.workdir_entry.get().strip()
        if new_value == self.config_manager.working_directory:
            return
        self.config_manager.set_working_directory(new_value)
        self._log(t("workdir.changed", path=new_value or t("workdir.empty")))

    def _browse_workdir(self) -> None:
        """폴더 선택 다이얼로그를 띄워 전역 작업 폴더를 지정."""
        initial = self.workdir_entry.get().strip() or os.path.expanduser("~")
        if not os.path.isdir(initial):
            initial = os.path.expanduser("~")
        chosen = filedialog.askdirectory(
            title=t("workdir.browse_title"),
            initialdir=initial, parent=self,
        )
        if chosen:
            self.workdir_entry.delete(0, "end")
            self.workdir_entry.insert(0, chosen)
            self.config_manager.set_working_directory(chosen)
            self._log(t("workdir.changed", path=chosen))

    # -------------------------------------------------- 레이아웃 / 창 상태
    def _on_layout_change(self, display_value: str) -> None:
        """레이아웃 드롭다운 변경 → 즉시 저장."""
        key = self._layout_display_to_key.get(display_value, "tabs")
        self.config_manager.set_layout_mode(key)
        self._log(t("layout.changed", value=display_value))

    def _on_wstate_change(self, display_value: str) -> None:
        """창 상태 드롭다운 변경 → 즉시 저장."""
        key = self._wstate_display_to_key.get(display_value, "normal")
        self.config_manager.set_window_state(key)
        self._log(t("wstate.changed", value=display_value))

    # ---------------------------------------------------------------- 실행/종료
    def _on_start(self) -> None:
        """작업 시작 — 활성 인스턴스를 모두 실행."""
        self._save_workdir_from_entry()

        workdir = self.config_manager.working_directory
        if not workdir:
            messagebox.showwarning(
                t("msg.workdir_missing_title"), t("msg.workdir_missing_body"),
            )
            return
        if not os.path.isdir(workdir):
            messagebox.showerror(
                t("msg.workdir_invalid_title"),
                t("msg.workdir_invalid_body", path=workdir),
            )
            return

        targets = [i for i in self.config_manager.instances if i.enabled]
        if not targets:
            messagebox.showinfo(t("msg.info_title"), t("msg.no_active_instances"))
            return

        if not is_claude_cli_available():
            messagebox.showerror(t("msg.cli_missing_title"), t("msg.cli_missing_body"))
            return

        if not messagebox.askyesno(
            t("msg.run_confirm_title"),
            t("msg.run_confirm_body", count=len(targets), workdir=workdir),
        ):
            return

        layout = self.config_manager.layout_mode
        wstate = self.config_manager.window_state
        self._log(t(
            "log.start_header",
            count=len(targets), workdir=workdir, layout=layout, wstate=wstate,
        ))
        results: List[LaunchResult] = launch_all(
            self.config_manager.instances, workdir,
            layout_mode=layout, window_state=wstate,
        )
        success_count = sum(1 for r in results if r.success)
        for r in results:
            prefix = "✔" if r.success else "✘"
            level = "info" if r.success else "error"
            self._log(f"  {prefix} [{r.instance_name}] {r.message}", level=level)
        self._log(t("log.start_done", success=success_count, total=len(results)))

    def _on_terminate_all(self) -> None:
        """실행 중인 모든 claude 프로세스를 종료."""
        if not messagebox.askyesno(
            t("msg.terminate_confirm_title"), t("msg.terminate_confirm_body"),
        ):
            return
        ok, msg = terminate_all()
        level = "info" if ok else "error"
        self._log(t("log.terminate_done", message=msg), level=level)

    # ------------------------------------------------------------------- 로깅
    def _log(self, message: str, level: str = "info") -> None:
        """로그 텍스트박스에 한 줄 추가하고 자동 스크롤. 버퍼에도 보존(언어 재구성용)."""
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"
        self._log_buffer.append(line)
        try:
            self.log_text.configure(state="normal")
            self.log_text.insert("end", line)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        except Exception:
            # _build_ui 전 호출 시(거의 없음) 무시
            pass
        try:
            print(line, end="")
        except Exception:
            pass


def main() -> int:
    """앱 진입점. 예외를 마지막에 받아 친절하게 표시한다."""
    try:
        app = App()
        app.mainloop()
    except Exception as e:  # pragma: no cover
        try:
            messagebox.showerror(t("msg.fatal_title"), str(e))
        except Exception:
            print(f"FATAL: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
