"""인스턴스 추가/수정 다이얼로그.

작업 디렉토리는 앱 전역에서 단일 값으로 관리하므로 이 폼에는 포함하지 않는다.

사용법:
    dialog = InstanceDialog(parent, instance=None)        # 추가
    dialog = InstanceDialog(parent, instance=existing)    # 수정
    parent.wait_window(dialog)
    if dialog.result is not None:
        ...
"""

from __future__ import annotations

from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from config_manager import Instance
from i18n import t


class InstanceDialog(ctk.CTkToplevel):
    """인스턴스 한 개를 추가하거나 수정하는 모달 다이얼로그."""

    def __init__(
        self,
        parent: ctk.CTk,
        instance: Optional[Instance] = None,
    ) -> None:
        super().__init__(parent)
        self.parent = parent
        self.is_edit_mode = instance is not None
        self.result: Optional[Instance] = None  # 저장 시 채워지고, 취소면 None 유지

        title = t("dialog.title_edit") if self.is_edit_mode else t("dialog.title_add")
        self.title(title)
        self.geometry("640x640")
        self.minsize(560, 560)

        # 모달 동작
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._build_ui()

        if instance is not None:
            self._populate(instance)

    # ----------------------------------------------------------------- UI 구성
    def _build_ui(self) -> None:
        """폼 위젯 배치."""
        container = ctk.CTkScrollableFrame(self, corner_radius=0)
        container.pack(fill="both", expand=True, padx=16, pady=(16, 0))

        row = 0

        # --- 이름
        ctk.CTkLabel(container, text=t("dialog.name"), anchor="w").grid(
            row=row, column=0, sticky="ew", pady=(0, 4))
        row += 1
        self.name_entry = ctk.CTkEntry(container, placeholder_text=t("dialog.name_placeholder"))
        self.name_entry.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        # --- 역할
        ctk.CTkLabel(container, text=t("dialog.role"), anchor="w").grid(
            row=row, column=0, sticky="ew", pady=(0, 4))
        row += 1
        self.role_entry = ctk.CTkEntry(container, placeholder_text=t("dialog.role_placeholder"))
        self.role_entry.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        # --- 시스템 프롬프트
        ctk.CTkLabel(container, text=t("dialog.system_prompt"), anchor="w").grid(
            row=row, column=0, sticky="ew", pady=(0, 4))
        row += 1
        self.system_prompt_text = ctk.CTkTextbox(container, height=160, wrap="word")
        self.system_prompt_text.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        # --- 초기 프롬프트
        ctk.CTkLabel(container, text=t("dialog.initial_prompt"), anchor="w").grid(
            row=row, column=0, sticky="ew", pady=(0, 4))
        row += 1
        self.initial_prompt_text = ctk.CTkTextbox(container, height=160, wrap="word")
        self.initial_prompt_text.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        # --- 모델 (선택)
        ctk.CTkLabel(container, text=t("dialog.model"), anchor="w").grid(
            row=row, column=0, sticky="ew", pady=(0, 4))
        row += 1
        self.model_entry = ctk.CTkEntry(
            container, placeholder_text=t("dialog.model_placeholder"))
        self.model_entry.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        # --- 활성화
        self.enabled_var = ctk.BooleanVar(value=True)
        self.enabled_check = ctk.CTkCheckBox(
            container, text=t("dialog.enabled"), variable=self.enabled_var)
        self.enabled_check.grid(row=row, column=0, sticky="w", pady=(4, 12))
        row += 1

        # 안내 문구
        info = ctk.CTkLabel(
            container,
            text=t("dialog.workdir_note"),
            text_color=("gray35", "gray65"), anchor="w",
        )
        info.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        row += 1

        container.grid_columnconfigure(0, weight=1)

        # 하단 버튼 바
        button_bar = ctk.CTkFrame(self, fg_color="transparent")
        button_bar.pack(fill="x", padx=16, pady=12)
        ctk.CTkButton(
            button_bar, text=t("dialog.cancel"), width=110, fg_color="gray40",
            hover_color="gray30", command=self._on_cancel,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            button_bar, text=t("dialog.save"), width=110, command=self._on_save,
        ).pack(side="right")

    # --------------------------------------------------------- 기존 값 채우기
    def _populate(self, instance: Instance) -> None:
        """수정 모드일 때 기존 인스턴스 값을 위젯에 채워넣는다."""
        self.name_entry.insert(0, instance.name)
        self.role_entry.insert(0, instance.role)
        self.system_prompt_text.insert("1.0", instance.system_prompt)
        self.initial_prompt_text.insert("1.0", instance.initial_prompt)
        self.model_entry.insert(0, instance.model)
        self.enabled_var.set(instance.enabled)

    # ------------------------------------------------------------------- 액션
    def _on_save(self) -> None:
        """폼 검증 후 self.result에 Instance를 채우고 창을 닫는다."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning(
                t("dialog.name_required_title"),
                t("dialog.name_required_body"),
                parent=self,
            )
            return

        self.result = Instance(
            name=name,
            role=self.role_entry.get().strip(),
            system_prompt=self.system_prompt_text.get("1.0", "end").strip(),
            initial_prompt=self.initial_prompt_text.get("1.0", "end").strip(),
            model=self.model_entry.get().strip(),
            enabled=bool(self.enabled_var.get()),
        )
        self.grab_release()
        self.destroy()

    def _on_cancel(self) -> None:
        """취소: 결과를 None으로 두고 창을 닫는다."""
        self.result = None
        self.grab_release()
        self.destroy()
