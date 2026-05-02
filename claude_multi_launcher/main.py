"""Claude Code Multi Launcher - 메인 GUI.

여러 Claude Code 인스턴스를 한 번의 클릭으로 동시 실행하기 위한 customtkinter
기반 데스크톱 앱.

기능 요약:
- 인스턴스 목록 (활성/비활성 체크박스)
- 작업시작 / 인스턴스 추가/수정/삭제 / 전체 종료 버튼
- 더블클릭 → 수정, 우클릭 → 컨텍스트 메뉴(복제/삭제/활성화 토글)
- 하단 실행 로그 영역
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox
from typing import List, Optional

import customtkinter as ctk

from config_manager import ConfigManager, Instance
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


class InstanceRow(ctk.CTkFrame):
    """인스턴스 한 줄을 표시하는 위젯.

    좌측: 활성화 체크박스
    중앙: 이름/역할(상단), 모델 등 부가정보(하단)
    """

    def __init__(
        self,
        master,
        index: int,
        instance: Instance,
        on_toggle,            # callable(index, bool)
        on_double_click,      # callable(index)
        on_right_click,       # callable(index, x, y)
    ) -> None:
        super().__init__(master, corner_radius=6)
        self.index = index
        self.instance = instance

        # 체크박스
        self.enabled_var = ctk.BooleanVar(value=instance.enabled)
        self.check = ctk.CTkCheckBox(
            self, text="", width=24, variable=self.enabled_var,
            command=lambda: on_toggle(self.index, bool(self.enabled_var.get())),
        )
        self.check.grid(row=0, column=0, rowspan=2, padx=(10, 8), pady=8, sticky="ns")

        # 이름 + 역할
        title_text = instance.name if instance.name else "(이름 없음)"
        if instance.role:
            title_text = f"{title_text}  —  {instance.role}"
        self.name_label = ctk.CTkLabel(
            self, text=title_text, anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.name_label.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(8, 0))

        # 부제: 모델 / 초기 프롬프트 한 줄 미리보기
        preview = (instance.initial_prompt or "").splitlines()
        preview_text = preview[0] if preview else ""
        if len(preview_text) > 80:
            preview_text = preview_text[:80] + "…"
        sub_parts: list[str] = []
        if instance.model:
            sub_parts.append(f"[{instance.model}]")
        if preview_text:
            sub_parts.append(preview_text)
        sub_text = "  ".join(sub_parts) if sub_parts else "(설명 없음)"

        self.sub_label = ctk.CTkLabel(
            self, text=sub_text, anchor="w", text_color=("gray30", "gray70"),
            font=ctk.CTkFont(size=11),
        )
        self.sub_label.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 8))

        self.grid_columnconfigure(1, weight=1)

        # 이벤트 바인딩
        for w in (self, self.name_label, self.sub_label):
            w.bind("<Double-Button-1>", lambda e: on_double_click(self.index))
            w.bind("<Button-3>", lambda e: on_right_click(self.index, e.x_root, e.y_root))


class App(ctk.CTk):
    """메인 애플리케이션 윈도우."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Claude Code Multi Launcher")
        self.geometry("960x720")
        self.minsize(820, 600)

        # 설정 로드
        self.config_manager = ConfigManager()
        try:
            self.config_manager.load()
        except RuntimeError as e:
            messagebox.showerror("설정 파일 오류", str(e))
            self.config_manager.instances = []

        # 비어 있으면 샘플 시드
        self.config_manager.ensure_sample_data()

        self._build_ui()
        self._refresh_list()

        # 시작 시 claude CLI 존재 여부 점검
        if not is_claude_cli_available():
            self._log(
                "⚠ claude CLI를 찾을 수 없습니다. Claude Code를 먼저 설치하세요: "
                "npm install -g @anthropic-ai/claude-code",
                level="warn",
            )

    # ----------------------------------------------------------------- UI 구성
    def _build_ui(self) -> None:
        """전체 레이아웃 구성."""
        # ---- 상단 헤더
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray85", "gray20"))
        header.pack(fill="x", side="top")

        title = ctk.CTkLabel(
            header, text="Claude Code Multi Launcher",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(side="left", padx=20, pady=14)

        subtitle = ctk.CTkLabel(
            header, text="여러 Claude 인스턴스를 한 번에 실행",
            text_color=("gray30", "gray70"),
        )
        subtitle.pack(side="left", padx=(0, 20), pady=14)

        # ---- 전역 작업 폴더 바 (모든 인스턴스 공통)
        workdir_bar = ctk.CTkFrame(self, corner_radius=8)
        workdir_bar.pack(fill="x", padx=16, pady=(12, 0))
        workdir_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            workdir_bar, text="작업 폴더 (공통)",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")

        self.workdir_entry = ctk.CTkEntry(
            workdir_bar, placeholder_text="모든 인스턴스가 공유할 작업 폴더를 지정하세요",
        )
        self.workdir_entry.grid(row=0, column=1, padx=(0, 8), pady=10, sticky="ew")
        self.workdir_entry.insert(0, self.config_manager.working_directory or "")
        self.workdir_entry.bind("<FocusOut>", lambda e: self._save_workdir_from_entry())
        self.workdir_entry.bind("<Return>", lambda e: self._save_workdir_from_entry())

        ctk.CTkButton(
            workdir_bar, text="📁 찾아보기", width=110,
            command=self._browse_workdir,
        ).grid(row=0, column=2, padx=(0, 12), pady=10)

        # ---- 레이아웃 / 창 상태 옵션 바 (Windows Terminal 한정)
        layout_bar = ctk.CTkFrame(self, corner_radius=8)
        layout_bar.pack(fill="x", padx=16, pady=(8, 0))

        ctk.CTkLabel(
            layout_bar, text="레이아웃",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")

        # 표시용 한글 ↔ 내부 키 매핑
        self._layout_display_to_key = {
            "탭으로 (한 창)": "tabs",
            "세로 분할 (좌우)": "split_vertical",
            "가로 분할 (상하)": "split_horizontal",
            "각각 별창": "separate",
        }
        self._layout_key_to_display = {v: k for k, v in self._layout_display_to_key.items()}

        self.layout_menu = ctk.CTkOptionMenu(
            layout_bar,
            values=list(self._layout_display_to_key.keys()),
            width=180,
            command=self._on_layout_change,
        )
        self.layout_menu.set(
            self._layout_key_to_display.get(self.config_manager.layout_mode, "탭으로 (한 창)")
        )
        self.layout_menu.grid(row=0, column=1, padx=(0, 16), pady=10, sticky="w")

        ctk.CTkLabel(
            layout_bar, text="창 상태",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=2, padx=(0, 8), pady=10, sticky="w")

        self._wstate_display_to_key = {
            "기본": "normal",
            "최대화": "maximized",
            "전체화면": "fullscreen",
        }
        self._wstate_key_to_display = {v: k for k, v in self._wstate_display_to_key.items()}

        self.wstate_menu = ctk.CTkOptionMenu(
            layout_bar,
            values=list(self._wstate_display_to_key.keys()),
            width=120,
            command=self._on_wstate_change,
        )
        self.wstate_menu.set(
            self._wstate_key_to_display.get(self.config_manager.window_state, "기본")
        )
        self.wstate_menu.grid(row=0, column=3, padx=(0, 12), pady=10, sticky="w")

        # 우측 안내
        ctk.CTkLabel(
            layout_bar,
            text="※ 분할/창 상태는 Windows Terminal(wt)이 설치된 경우에만 적용됩니다.",
            text_color=("gray35", "gray65"), font=ctk.CTkFont(size=11),
        ).grid(row=0, column=4, padx=(0, 12), pady=10, sticky="e")
        layout_bar.grid_columnconfigure(4, weight=1)

        # ---- 큰 작업시작 버튼 + 보조 버튼들
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=16, pady=(12, 0))

        # 메인 액션 (큼지막하게)
        self.start_btn = ctk.CTkButton(
            action_bar, text="▶  작업 시작 (활성 인스턴스 모두 실행)",
            height=52, font=ctk.CTkFont(size=16, weight="bold"),
            command=self._on_start,
        )
        self.start_btn.pack(side="left", fill="x", expand=True)

        # 우측 보조 액션
        self.terminate_btn = ctk.CTkButton(
            action_bar, text="■ 전체 종료", height=52, width=120,
            fg_color="#a83232", hover_color="#7a2424",
            command=self._on_terminate_all,
        )
        self.terminate_btn.pack(side="left", padx=(8, 0))

        # ---- CRUD 버튼
        crud_bar = ctk.CTkFrame(self, fg_color="transparent")
        crud_bar.pack(fill="x", padx=16, pady=(8, 0))
        ctk.CTkButton(crud_bar, text="＋ 인스턴스 추가", width=140,
                      command=self._on_add).pack(side="left")
        ctk.CTkButton(crud_bar, text="✎ 수정", width=100,
                      command=self._on_edit_selected).pack(side="left", padx=(8, 0))
        ctk.CTkButton(crud_bar, text="🗑 삭제", width=100,
                      fg_color="gray40", hover_color="gray30",
                      command=self._on_delete_selected).pack(side="left", padx=(8, 0))

        # 우측 안내 라벨
        hint = ctk.CTkLabel(
            crud_bar,
            text="더블클릭: 수정  •  우클릭: 메뉴",
            text_color=("gray35", "gray65"), font=ctk.CTkFont(size=11),
        )
        hint.pack(side="right", padx=(8, 0))

        # ---- 인스턴스 리스트 (스크롤)
        list_label = ctk.CTkLabel(
            self, text="등록된 인스턴스",
            anchor="w", font=ctk.CTkFont(size=13, weight="bold"),
        )
        list_label.pack(fill="x", padx=18, pady=(14, 4))

        self.list_frame = ctk.CTkScrollableFrame(self, height=320)
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        # ---- 로그 영역
        log_label = ctk.CTkLabel(
            self, text="실행 로그",
            anchor="w", font=ctk.CTkFont(size=13, weight="bold"),
        )
        log_label.pack(fill="x", padx=18, pady=(8, 4))

        self.log_text = ctk.CTkTextbox(self, height=160, wrap="word")
        self.log_text.pack(fill="both", expand=False, padx=16, pady=(0, 16))
        self.log_text.configure(state="disabled")

        # ---- 우클릭 컨텍스트 메뉴 (tk.Menu 사용 — CTk엔 Menu가 없음)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="수정", command=self._ctx_edit)
        self.context_menu.add_command(label="복제", command=self._ctx_duplicate)
        self.context_menu.add_command(label="활성화/비활성화 토글", command=self._ctx_toggle)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="삭제", command=self._ctx_delete)
        self._context_index: Optional[int] = None
        self._selected_index: Optional[int] = None

        # 행이 표시되는 영역의 레퍼런스
        self.row_widgets: List[InstanceRow] = []

    # ---------------------------------------------------------- 리스트 갱신/선택
    def _refresh_list(self) -> None:
        """ConfigManager의 인스턴스 리스트를 화면에 다시 그린다."""
        # 기존 위젯 제거
        for w in self.row_widgets:
            w.destroy()
        self.row_widgets.clear()

        if not self.config_manager.instances:
            empty = ctk.CTkLabel(
                self.list_frame,
                text="등록된 인스턴스가 없습니다. '＋ 인스턴스 추가'로 시작하세요.",
                text_color=("gray35", "gray65"),
            )
            empty.pack(pady=40)
            self.row_widgets.append(empty)
            return

        for i, inst in enumerate(self.config_manager.instances):
            row = InstanceRow(
                self.list_frame,
                index=i,
                instance=inst,
                on_toggle=self._on_row_toggle,
                on_double_click=self._on_row_double_click,
                on_right_click=self._on_row_right_click,
            )
            row.pack(fill="x", padx=4, pady=4)
            # 단일 클릭으로 선택 상태 표시 (간단히 _selected_index만 갱신)
            for sub in (row, row.name_label, row.sub_label):
                sub.bind("<Button-1>", lambda e, idx=i: self._select_row(idx))
            self.row_widgets.append(row)

        # 선택 인덱스가 범위를 벗어났으면 초기화
        if self._selected_index is not None and self._selected_index >= len(self.config_manager.instances):
            self._selected_index = None

        self._highlight_selected()

    def _select_row(self, index: int) -> None:
        """클릭으로 선택된 행 인덱스를 갱신하고 강조."""
        self._selected_index = index
        self._highlight_selected()

    def _highlight_selected(self) -> None:
        """선택된 행에 시각적 강조를 적용."""
        for w in self.row_widgets:
            if isinstance(w, InstanceRow):
                if self._selected_index is not None and w.index == self._selected_index:
                    w.configure(fg_color=("#cfe2ff", "#1f3a5f"))
                else:
                    # 기본 색으로 되돌리기
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
            self._log(f"인스턴스 복제: '{new_inst.name}'")
            self._refresh_list()
        except Exception as e:
            messagebox.showerror("오류", f"복제 실패: {e}")

    def _ctx_toggle(self) -> None:
        if self._context_index is None:
            return
        new_state = self.config_manager.toggle_enabled(self._context_index)
        self._log(
            f"인스턴스 '{self.config_manager.instances[self._context_index].name}' "
            f"→ {'활성화' if new_state else '비활성화'}"
        )
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
            self._log(f"인스턴스 추가: '{dialog.result.name}'")
            self._refresh_list()

    def _on_edit_selected(self) -> None:
        """'수정' 버튼 — 선택된 항목을 수정."""
        if self._selected_index is None:
            messagebox.showinfo("안내", "수정할 인스턴스를 먼저 선택하세요.")
            return
        self._edit_at(self._selected_index)

    def _edit_at(self, index: int) -> None:
        """인덱스에 해당하는 인스턴스를 수정 다이얼로그로 연다."""
        original = self.config_manager.instances[index]
        dialog = InstanceDialog(self, instance=original)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.config_manager.update(index, dialog.result)
            self._log(f"인스턴스 수정: '{dialog.result.name}'")
            self._refresh_list()

    def _on_delete_selected(self) -> None:
        """'삭제' 버튼 — 선택된 항목을 삭제."""
        if self._selected_index is None:
            messagebox.showinfo("안내", "삭제할 인스턴스를 먼저 선택하세요.")
            return
        self._delete_at(self._selected_index)

    def _delete_at(self, index: int) -> None:
        """확인 후 인덱스 위치의 인스턴스를 삭제한다."""
        inst = self.config_manager.instances[index]
        if not messagebox.askyesno(
            "삭제 확인", f"'{inst.name}' 인스턴스를 삭제하시겠습니까?"
        ):
            return
        self.config_manager.delete(index)
        self._log(f"인스턴스 삭제: '{inst.name}'")
        self._selected_index = None
        self._refresh_list()

    # ----------------------------------------------------------- 작업 폴더
    def _save_workdir_from_entry(self) -> None:
        """입력창의 값을 전역 작업 폴더로 저장."""
        new_value = self.workdir_entry.get().strip()
        if new_value == self.config_manager.working_directory:
            return
        self.config_manager.set_working_directory(new_value)
        self._log(f"작업 폴더 변경: {new_value or '(비움)'}")

    def _browse_workdir(self) -> None:
        """폴더 선택 다이얼로그를 띄워 전역 작업 폴더를 지정."""
        initial = self.workdir_entry.get().strip() or os.path.expanduser("~")
        if not os.path.isdir(initial):
            initial = os.path.expanduser("~")
        chosen = filedialog.askdirectory(
            title="작업 폴더 선택 (모든 인스턴스 공통)",
            initialdir=initial, parent=self,
        )
        if chosen:
            self.workdir_entry.delete(0, "end")
            self.workdir_entry.insert(0, chosen)
            self.config_manager.set_working_directory(chosen)
            self._log(f"작업 폴더 변경: {chosen}")

    # -------------------------------------------------- 레이아웃 / 창 상태
    def _on_layout_change(self, display_value: str) -> None:
        """레이아웃 드롭다운 변경 → 즉시 저장."""
        key = self._layout_display_to_key.get(display_value, "tabs")
        self.config_manager.set_layout_mode(key)
        self._log(f"레이아웃 변경: {display_value}")

    def _on_wstate_change(self, display_value: str) -> None:
        """창 상태 드롭다운 변경 → 즉시 저장."""
        key = self._wstate_display_to_key.get(display_value, "normal")
        self.config_manager.set_window_state(key)
        self._log(f"창 상태 변경: {display_value}")

    # ---------------------------------------------------------------- 실행/종료
    def _on_start(self) -> None:
        """작업 시작 — 활성 인스턴스를 모두 실행."""
        # 입력창에 마지막으로 입력된 값을 먼저 반영
        self._save_workdir_from_entry()

        workdir = self.config_manager.working_directory
        if not workdir:
            messagebox.showwarning(
                "작업 폴더 미설정",
                "상단에서 작업 폴더를 먼저 지정하세요.",
            )
            return
        if not os.path.isdir(workdir):
            messagebox.showerror(
                "작업 폴더 오류",
                f"작업 폴더가 존재하지 않습니다:\n{workdir}",
            )
            return

        targets = [i for i in self.config_manager.instances if i.enabled]
        if not targets:
            messagebox.showinfo("안내", "활성화된 인스턴스가 없습니다. 체크박스로 활성화하세요.")
            return

        if not is_claude_cli_available():
            messagebox.showerror(
                "Claude CLI 미설치",
                "claude CLI를 찾을 수 없습니다.\n"
                "다음 명령으로 먼저 설치하세요:\n\n"
                "    npm install -g @anthropic-ai/claude-code",
            )
            return

        if not messagebox.askyesno(
            "실행 확인",
            f"{len(targets)}개의 Claude Code 인스턴스를\n"
            f"다음 폴더에서 실행합니다.\n\n{workdir}\n\n계속하시겠습니까?",
        ):
            return

        layout = self.config_manager.layout_mode
        wstate = self.config_manager.window_state
        self._log(
            f"━━ {len(targets)}개 인스턴스 실행 시작 "
            f"(폴더: {workdir} · 레이아웃: {layout} · 창: {wstate}) ━━"
        )
        results: List[LaunchResult] = launch_all(
            self.config_manager.instances, workdir,
            layout_mode=layout, window_state=wstate,
        )
        success_count = sum(1 for r in results if r.success)
        for r in results:
            prefix = "✔" if r.success else "✘"
            level = "info" if r.success else "error"
            self._log(f"  {prefix} [{r.instance_name}] {r.message}", level=level)
        self._log(f"━━ 완료: 성공 {success_count}/{len(results)} ━━")

    def _on_terminate_all(self) -> None:
        """실행 중인 모든 claude 프로세스를 종료."""
        if not messagebox.askyesno(
            "전체 종료",
            "실행 중인 모든 Claude Code 프로세스를 종료합니다.\n계속하시겠습니까?",
        ):
            return
        ok, msg = terminate_all()
        level = "info" if ok else "error"
        self._log(f"전체 종료: {msg}", level=level)

    # ------------------------------------------------------------------- 로깅
    def _log(self, message: str, level: str = "info") -> None:
        """로그 텍스트박스에 한 줄 추가하고 자동 스크롤."""
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        # 콘솔에도 동시에 출력 (디버깅용)
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
            messagebox.showerror("치명적 오류", str(e))
        except Exception:
            print(f"FATAL: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
