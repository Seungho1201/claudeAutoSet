"""다국어(i18n) 번역 모듈.

지원 언어: ko(한국어) / en(English) / ja(日本語)

사용:
    from i18n import t, set_language, current_language

    set_language("en")
    label.configure(text=t("app.title"))

키 이름 규칙: 점(.)으로 구분된 도메인. 예) app.title, button.start, dialog.save
샘플 인스턴스 데이터(이름/역할/프롬프트)는 사용자 콘텐츠로 보고 i18n 대상에서
제외한다 — 한국어로 시드되어 있어도 사용자가 자유롭게 수정 가능.
"""

from __future__ import annotations

from typing import Dict


SUPPORTED_LANGUAGES = ("ko", "en", "ja")
DEFAULT_LANGUAGE = "ko"

# 언어 코드 → 사용자에게 보일 표시명 (선택 패널에서 사용)
LANGUAGE_DISPLAY_NAMES: Dict[str, str] = {
    "ko": "한국어",
    "en": "English",
    "ja": "日本語",
}


_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ko": {
        # ----- 앱/헤더
        "app.title": "Claude Code Multi Launcher",
        "app.subtitle": "여러 Claude 인스턴스를 한 번에 실행",
        "app.settings_button": "⚙ 설정",

        # ----- 작업 폴더
        "workdir.label": "작업 폴더 (공통)",
        "workdir.placeholder": "모든 인스턴스가 공유할 작업 폴더를 지정하세요",
        "workdir.browse": "📁 찾아보기",
        "workdir.browse_title": "작업 폴더 선택 (모든 인스턴스 공통)",
        "workdir.changed": "작업 폴더 변경: {path}",
        "workdir.empty": "(비움)",

        # ----- 레이아웃 / 창 상태
        "layout.label": "레이아웃",
        "layout.tabs": "탭으로 (한 창)",
        "layout.split_vertical": "세로 분할 (좌우)",
        "layout.split_horizontal": "가로 분할 (상하)",
        "layout.separate": "각각 별창",
        "layout.changed": "레이아웃 변경: {value}",
        "wstate.label": "창 상태",
        "wstate.normal": "기본",
        "wstate.maximized": "최대화",
        "wstate.fullscreen": "전체화면",
        "wstate.changed": "창 상태 변경: {value}",
        "layout.note": "※ 분할/창 상태는 Windows Terminal(wt)이 설치된 경우에만 적용됩니다.",

        # ----- 메인 액션
        "action.start": "▶  작업 시작 (활성 인스턴스 모두 실행)",
        "action.terminate": "■ 전체 종료",

        # ----- CRUD
        "crud.add": "＋ 인스턴스 추가",
        "crud.edit": "✎ 수정",
        "crud.delete": "🗑 삭제",
        "crud.hint": "더블클릭: 수정  •  우클릭: 메뉴",

        # ----- 리스트
        "list.title": "등록된 인스턴스",
        "list.empty": "등록된 인스턴스가 없습니다. '＋ 인스턴스 추가'로 시작하세요.",
        "list.unnamed": "(이름 없음)",
        "list.no_description": "(설명 없음)",

        # ----- 컨텍스트 메뉴
        "ctx.edit": "수정",
        "ctx.duplicate": "복제",
        "ctx.toggle": "활성화/비활성화 토글",
        "ctx.delete": "삭제",
        "ctx.duplicated": "인스턴스 복제: '{name}'",
        "ctx.toggled_on": "활성화",
        "ctx.toggled_off": "비활성화",
        "ctx.toggle_log": "인스턴스 '{name}' → {state}",

        # ----- 로그
        "log.title": "실행 로그",
        "log.added": "인스턴스 추가: '{name}'",
        "log.updated": "인스턴스 수정: '{name}'",
        "log.deleted": "인스턴스 삭제: '{name}'",
        "log.start_header": "━━ {count}개 인스턴스 실행 시작 (폴더: {workdir} · 레이아웃: {layout} · 창: {wstate}) ━━",
        "log.start_done": "━━ 완료: 성공 {success}/{total} ━━",
        "log.terminate_done": "전체 종료: {message}",
        "log.cli_missing": "⚠ claude CLI를 찾을 수 없습니다. Claude Code를 먼저 설치하세요: npm install -g @anthropic-ai/claude-code",
        "log.language_changed": "언어 변경: {language}",

        # ----- 메시지박스
        "msg.config_error_title": "설정 파일 오류",
        "msg.info_title": "안내",
        "msg.error_title": "오류",
        "msg.warn_title": "경고",
        "msg.fatal_title": "치명적 오류",
        "msg.select_first_edit": "수정할 인스턴스를 먼저 선택하세요.",
        "msg.select_first_delete": "삭제할 인스턴스를 먼저 선택하세요.",
        "msg.delete_confirm_title": "삭제 확인",
        "msg.delete_confirm_body": "'{name}' 인스턴스를 삭제하시겠습니까?",
        "msg.duplicate_failed": "복제 실패: {error}",
        "msg.workdir_missing_title": "작업 폴더 미설정",
        "msg.workdir_missing_body": "상단에서 작업 폴더를 먼저 지정하세요.",
        "msg.workdir_invalid_title": "작업 폴더 오류",
        "msg.workdir_invalid_body": "작업 폴더가 존재하지 않습니다:\n{path}",
        "msg.no_active_instances": "활성화된 인스턴스가 없습니다. 체크박스로 활성화하세요.",
        "msg.cli_missing_title": "Claude CLI 미설치",
        "msg.cli_missing_body": "claude CLI를 찾을 수 없습니다.\n다음 명령으로 먼저 설치하세요:\n\n    npm install -g @anthropic-ai/claude-code",
        "msg.run_confirm_title": "실행 확인",
        "msg.run_confirm_body": "{count}개의 Claude Code 인스턴스를\n다음 폴더에서 실행합니다.\n\n{workdir}\n\n계속하시겠습니까?",
        "msg.terminate_confirm_title": "전체 종료",
        "msg.terminate_confirm_body": "실행 중인 모든 Claude Code 프로세스를 종료합니다.\n계속하시겠습니까?",

        # ----- 설정 패널 (하단 팝업)
        "settings.title": "설정",
        "settings.language_label": "언어 / Language / 言語",
        "settings.close": "닫기",

        # ----- 인스턴스 다이얼로그
        "dialog.title_add": "새 인스턴스 추가",
        "dialog.title_edit": "인스턴스 수정",
        "dialog.name": "인스턴스 이름 *",
        "dialog.name_placeholder": "예: 프론트엔드 담당",
        "dialog.role": "역할",
        "dialog.role_placeholder": "예: React 개발자",
        "dialog.system_prompt": "시스템 프롬프트 (--append-system-prompt)",
        "dialog.initial_prompt": "초기 작업 지시 프롬프트",
        "dialog.model": "모델 (선택사항, 비우면 기본값)",
        "dialog.model_placeholder": "예: claude-opus-4-7 / claude-sonnet-4-6",
        "dialog.enabled": "실행 시 포함 (활성화)",
        "dialog.workdir_note": "※ 작업 폴더는 메인 화면 상단에서 모든 인스턴스 공통으로 설정합니다.",
        "dialog.save": "저장",
        "dialog.cancel": "취소",
        "dialog.name_required_title": "입력 오류",
        "dialog.name_required_body": "인스턴스 이름은 필수입니다.",

        # ----- 복제 접미사
        "copy_suffix": " (복사)",
    },

    "en": {
        "app.title": "Claude Code Multi Launcher",
        "app.subtitle": "Run multiple Claude instances at once",
        "app.settings_button": "⚙ Settings",

        "workdir.label": "Working Folder (shared)",
        "workdir.placeholder": "Folder all instances will share",
        "workdir.browse": "📁 Browse",
        "workdir.browse_title": "Choose Working Folder (shared by all instances)",
        "workdir.changed": "Working folder changed: {path}",
        "workdir.empty": "(empty)",

        "layout.label": "Layout",
        "layout.tabs": "Tabs (one window)",
        "layout.split_vertical": "Vertical split (left/right)",
        "layout.split_horizontal": "Horizontal split (top/bottom)",
        "layout.separate": "Separate windows",
        "layout.changed": "Layout changed: {value}",
        "wstate.label": "Window State",
        "wstate.normal": "Normal",
        "wstate.maximized": "Maximized",
        "wstate.fullscreen": "Fullscreen",
        "wstate.changed": "Window state changed: {value}",
        "layout.note": "* Split / window state apply only when Windows Terminal (wt) is installed.",

        "action.start": "▶  Start (run all enabled instances)",
        "action.terminate": "■ Terminate All",

        "crud.add": "＋ Add Instance",
        "crud.edit": "✎ Edit",
        "crud.delete": "🗑 Delete",
        "crud.hint": "Double-click: edit  •  Right-click: menu",

        "list.title": "Registered Instances",
        "list.empty": "No instances registered. Use '＋ Add Instance' to start.",
        "list.unnamed": "(unnamed)",
        "list.no_description": "(no description)",

        "ctx.edit": "Edit",
        "ctx.duplicate": "Duplicate",
        "ctx.toggle": "Toggle Enabled",
        "ctx.delete": "Delete",
        "ctx.duplicated": "Instance duplicated: '{name}'",
        "ctx.toggled_on": "enabled",
        "ctx.toggled_off": "disabled",
        "ctx.toggle_log": "Instance '{name}' → {state}",

        "log.title": "Run Log",
        "log.added": "Instance added: '{name}'",
        "log.updated": "Instance updated: '{name}'",
        "log.deleted": "Instance deleted: '{name}'",
        "log.start_header": "━━ Starting {count} instance(s) (folder: {workdir} · layout: {layout} · window: {wstate}) ━━",
        "log.start_done": "━━ Done: {success}/{total} succeeded ━━",
        "log.terminate_done": "Terminate all: {message}",
        "log.cli_missing": "⚠ claude CLI not found. Please install Claude Code first: npm install -g @anthropic-ai/claude-code",
        "log.language_changed": "Language changed: {language}",

        "msg.config_error_title": "Config File Error",
        "msg.info_title": "Info",
        "msg.error_title": "Error",
        "msg.warn_title": "Warning",
        "msg.fatal_title": "Fatal Error",
        "msg.select_first_edit": "Select an instance to edit first.",
        "msg.select_first_delete": "Select an instance to delete first.",
        "msg.delete_confirm_title": "Confirm Delete",
        "msg.delete_confirm_body": "Delete instance '{name}'?",
        "msg.duplicate_failed": "Duplicate failed: {error}",
        "msg.workdir_missing_title": "Working Folder Not Set",
        "msg.workdir_missing_body": "Please specify the working folder at the top first.",
        "msg.workdir_invalid_title": "Working Folder Error",
        "msg.workdir_invalid_body": "Working folder does not exist:\n{path}",
        "msg.no_active_instances": "No enabled instances. Enable some via the checkboxes.",
        "msg.cli_missing_title": "Claude CLI Not Installed",
        "msg.cli_missing_body": "claude CLI not found.\nInstall it first with:\n\n    npm install -g @anthropic-ai/claude-code",
        "msg.run_confirm_title": "Confirm Run",
        "msg.run_confirm_body": "Run {count} Claude Code instance(s) in:\n\n{workdir}\n\nContinue?",
        "msg.terminate_confirm_title": "Terminate All",
        "msg.terminate_confirm_body": "Terminate all running Claude Code processes.\nContinue?",

        "settings.title": "Settings",
        "settings.language_label": "Language / 언어 / 言語",
        "settings.close": "Close",

        "dialog.title_add": "Add New Instance",
        "dialog.title_edit": "Edit Instance",
        "dialog.name": "Instance Name *",
        "dialog.name_placeholder": "e.g. Frontend Lead",
        "dialog.role": "Role",
        "dialog.role_placeholder": "e.g. React developer",
        "dialog.system_prompt": "System Prompt (--append-system-prompt)",
        "dialog.initial_prompt": "Initial Task Prompt",
        "dialog.model": "Model (optional, blank = default)",
        "dialog.model_placeholder": "e.g. claude-opus-4-7 / claude-sonnet-4-6",
        "dialog.enabled": "Include on run (enabled)",
        "dialog.workdir_note": "* The working folder is set on the main screen, shared by all instances.",
        "dialog.save": "Save",
        "dialog.cancel": "Cancel",
        "dialog.name_required_title": "Input Error",
        "dialog.name_required_body": "Instance name is required.",

        "copy_suffix": " (copy)",
    },

    "ja": {
        "app.title": "Claude Code Multi Launcher",
        "app.subtitle": "複数のClaudeインスタンスを一度に起動",
        "app.settings_button": "⚙ 設定",

        "workdir.label": "作業フォルダ (共通)",
        "workdir.placeholder": "すべてのインスタンスで共有する作業フォルダ",
        "workdir.browse": "📁 参照",
        "workdir.browse_title": "作業フォルダを選択 (全インスタンス共通)",
        "workdir.changed": "作業フォルダ変更: {path}",
        "workdir.empty": "(未設定)",

        "layout.label": "レイアウト",
        "layout.tabs": "タブ (1ウィンドウ)",
        "layout.split_vertical": "縦分割 (左右)",
        "layout.split_horizontal": "横分割 (上下)",
        "layout.separate": "別々のウィンドウ",
        "layout.changed": "レイアウト変更: {value}",
        "wstate.label": "ウィンドウ状態",
        "wstate.normal": "通常",
        "wstate.maximized": "最大化",
        "wstate.fullscreen": "全画面",
        "wstate.changed": "ウィンドウ状態変更: {value}",
        "layout.note": "※ 分割 / ウィンドウ状態は Windows Terminal(wt) が必要です。",

        "action.start": "▶  起動 (有効なインスタンスをすべて実行)",
        "action.terminate": "■ すべて終了",

        "crud.add": "＋ インスタンス追加",
        "crud.edit": "✎ 編集",
        "crud.delete": "🗑 削除",
        "crud.hint": "ダブルクリック: 編集  •  右クリック: メニュー",

        "list.title": "登録済みインスタンス",
        "list.empty": "インスタンスが登録されていません。'＋ インスタンス追加' から始めてください。",
        "list.unnamed": "(名前なし)",
        "list.no_description": "(説明なし)",

        "ctx.edit": "編集",
        "ctx.duplicate": "複製",
        "ctx.toggle": "有効/無効を切り替え",
        "ctx.delete": "削除",
        "ctx.duplicated": "インスタンスを複製: '{name}'",
        "ctx.toggled_on": "有効",
        "ctx.toggled_off": "無効",
        "ctx.toggle_log": "インスタンス '{name}' → {state}",

        "log.title": "実行ログ",
        "log.added": "インスタンス追加: '{name}'",
        "log.updated": "インスタンス更新: '{name}'",
        "log.deleted": "インスタンス削除: '{name}'",
        "log.start_header": "━━ {count}個のインスタンスを起動 (フォルダ: {workdir} · レイアウト: {layout} · ウィンドウ: {wstate}) ━━",
        "log.start_done": "━━ 完了: 成功 {success}/{total} ━━",
        "log.terminate_done": "全終了: {message}",
        "log.cli_missing": "⚠ claude CLI が見つかりません。Claude Code を先にインストールしてください: npm install -g @anthropic-ai/claude-code",
        "log.language_changed": "言語変更: {language}",

        "msg.config_error_title": "設定ファイルエラー",
        "msg.info_title": "情報",
        "msg.error_title": "エラー",
        "msg.warn_title": "警告",
        "msg.fatal_title": "致命的エラー",
        "msg.select_first_edit": "編集するインスタンスを先に選択してください。",
        "msg.select_first_delete": "削除するインスタンスを先に選択してください。",
        "msg.delete_confirm_title": "削除確認",
        "msg.delete_confirm_body": "インスタンス '{name}' を削除しますか?",
        "msg.duplicate_failed": "複製失敗: {error}",
        "msg.workdir_missing_title": "作業フォルダ未設定",
        "msg.workdir_missing_body": "上部で作業フォルダを先に指定してください。",
        "msg.workdir_invalid_title": "作業フォルダエラー",
        "msg.workdir_invalid_body": "作業フォルダが存在しません:\n{path}",
        "msg.no_active_instances": "有効なインスタンスがありません。チェックボックスで有効化してください。",
        "msg.cli_missing_title": "Claude CLI 未インストール",
        "msg.cli_missing_body": "claude CLI が見つかりません。\n次のコマンドでインストールしてください:\n\n    npm install -g @anthropic-ai/claude-code",
        "msg.run_confirm_title": "実行確認",
        "msg.run_confirm_body": "{count}個の Claude Code インスタンスを次のフォルダで実行します。\n\n{workdir}\n\n続けますか?",
        "msg.terminate_confirm_title": "全終了",
        "msg.terminate_confirm_body": "実行中の全 Claude Code プロセスを終了します。\n続けますか?",

        "settings.title": "設定",
        "settings.language_label": "言語 / 언어 / Language",
        "settings.close": "閉じる",

        "dialog.title_add": "新規インスタンス追加",
        "dialog.title_edit": "インスタンス編集",
        "dialog.name": "インスタンス名 *",
        "dialog.name_placeholder": "例: フロントエンド担当",
        "dialog.role": "役割",
        "dialog.role_placeholder": "例: React開発者",
        "dialog.system_prompt": "システムプロンプト (--append-system-prompt)",
        "dialog.initial_prompt": "初期タスクプロンプト",
        "dialog.model": "モデル (任意。空欄ならデフォルト)",
        "dialog.model_placeholder": "例: claude-opus-4-7 / claude-sonnet-4-6",
        "dialog.enabled": "実行に含める (有効)",
        "dialog.workdir_note": "※ 作業フォルダはメイン画面上部で全インスタンス共通に設定します。",
        "dialog.save": "保存",
        "dialog.cancel": "キャンセル",
        "dialog.name_required_title": "入力エラー",
        "dialog.name_required_body": "インスタンス名は必須です。",

        "copy_suffix": " (コピー)",
    },
}


# 현재 활성 언어 — set_language()로 변경
_current: str = DEFAULT_LANGUAGE


def current_language() -> str:
    """현재 활성 언어 코드 반환."""
    return _current


def set_language(lang: str) -> None:
    """현재 언어를 변경. 지원되지 않는 코드는 기본값으로 폴백."""
    global _current
    _current = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def t(key: str, **kwargs) -> str:
    """현재 언어로 키를 번역. 없으면 한국어 폴백 → 그래도 없으면 키 자체 반환.

    placeholders는 .format(**kwargs)로 치환된다.
    """
    table = _TRANSLATIONS.get(_current) or _TRANSLATIONS[DEFAULT_LANGUAGE]
    text = table.get(key)
    if text is None:
        text = _TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
