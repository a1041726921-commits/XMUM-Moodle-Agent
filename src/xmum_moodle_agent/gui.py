# -*- coding: utf-8 -*-
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .gui_state import GuiSettings, can_generate_notes, load_gui_settings, save_gui_settings


class MoodleAgentGui(tk.Tk):
    def __init__(self, root_path: Path):
        super().__init__()
        self.root_path = root_path.resolve()
        self.settings = load_gui_settings(self.root_path)
        self.title("XMUM Moodle Agent")
        self.geometry("880x580")
        self.minsize(760, 520)

        self.username_var = tk.StringVar(value=self.settings.moodle_username)
        self.password_var = tk.StringVar(value=self.settings.moodle_password)
        self.remember_password_var = tk.BooleanVar(value=self.settings.remember_password)
        self.auto_login_var = tk.BooleanVar(value=self.settings.auto_login)
        self.generate_notes_var = tk.BooleanVar(value=False)
        self.selected_provider_var = tk.StringVar(value=self._first_connected_provider_id())
        self.status_var = tk.StringVar(value="准备就绪")
        self.api_status_var = tk.StringVar(value=self._api_status_text())

        self._configure_style()
        self._build_layout()
        self._refresh_note_controls()

        if self.settings.auto_login and self.settings.moodle_username and self.settings.moodle_password:
            self.after(600, self._run_check_login)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f6f7f9")
        style.configure("Panel.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("TLabel", background="#f6f7f9", foreground="#1d2433", font=("Microsoft YaHei UI", 10))
        style.configure("Panel.TLabel", background="#ffffff", foreground="#1d2433", font=("Microsoft YaHei UI", 10))
        style.configure("Title.TLabel", background="#f6f7f9", foreground="#111827", font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Hint.TLabel", background="#ffffff", foreground="#667085", font=("Microsoft YaHei UI", 9))
        style.configure("Status.TLabel", background="#eef2f6", foreground="#344054", font=("Microsoft YaHei UI", 9))
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(12, 7))
        style.configure("Accent.TButton", font=("Microsoft YaHei UI", 10, "bold"), padding=(14, 8))
        style.configure("TCheckbutton", background="#ffffff", foreground="#1d2433", font=("Microsoft YaHei UI", 10))
        style.configure("TNotebook", background="#f6f7f9", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Microsoft YaHei UI", 10), padding=(18, 8))

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=24)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="XMUM Moodle Agent 控制台", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            container,
            text="配置 Moodle 登录、模型 API，并决定是否启用模型辅助生成笔记。",
        ).pack(anchor="w", pady=(6, 18))

        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)

        moodle_tab = ttk.Frame(notebook, padding=18)
        notes_tab = ttk.Frame(notebook, padding=18)
        notebook.add(moodle_tab, text="Moodle 登录")
        notebook.add(notes_tab, text="笔记生成")

        self._build_moodle_tab(moodle_tab)
        self._build_notes_tab(notes_tab)

        status = ttk.Label(container, textvariable=self.status_var, style="Status.TLabel", padding=(12, 8))
        status.pack(fill="x", pady=(14, 0))

    def _build_moodle_tab(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        panel.pack(fill="x", anchor="n")

        ttk.Label(panel, text="Campus ID / Moodle 账号", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        username = ttk.Entry(panel, textvariable=self.username_var, width=42)
        username.grid(row=1, column=0, sticky="ew", pady=(6, 14))

        ttk.Label(panel, text="Moodle 密码", style="Panel.TLabel").grid(row=2, column=0, sticky="w")
        password = ttk.Entry(panel, textvariable=self.password_var, show="*", width=42)
        password.grid(row=3, column=0, sticky="ew", pady=(6, 14))

        ttk.Checkbutton(panel, text="记住密码（写入本地 .env）", variable=self.remember_password_var).grid(
            row=4, column=0, sticky="w", pady=(0, 8)
        )
        ttk.Checkbutton(panel, text="打开程序后自动登录检查", variable=self.auto_login_var).grid(
            row=5, column=0, sticky="w", pady=(0, 16)
        )

        button_row = ttk.Frame(panel, style="Panel.TFrame")
        button_row.grid(row=6, column=0, sticky="w")
        ttk.Button(button_row, text="保存登录配置", style="Accent.TButton", command=self._save_moodle).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(button_row, text="检查 Moodle 登录", command=self._run_check_login).pack(side="left")

        ttk.Label(
            panel,
            text="不勾选记住密码时，密码只保留在当前窗口中；保存后 .env 会留下空密码。",
            style="Hint.TLabel",
        ).grid(row=7, column=0, sticky="w", pady=(18, 0))
        panel.columnconfigure(0, weight=1)

    def _build_notes_tab(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        panel.pack(fill="x", anchor="n")

        ttk.Label(panel, textvariable=self.api_status_var, style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(panel, text="打开模型 API 接入窗口", style="Accent.TButton", command=self._open_api_window).grid(
            row=1, column=0, sticky="w", pady=(12, 18)
        )

        self.generate_notes_check = ttk.Checkbutton(
            panel,
            text="使用已接入的模型 API 生成笔记",
            variable=self.generate_notes_var,
        )
        self.generate_notes_check.grid(row=2, column=0, sticky="w", pady=(0, 12))

        ttk.Label(panel, text="选择模型提供商", style="Panel.TLabel").grid(row=3, column=0, sticky="w")
        self.provider_combo = ttk.Combobox(
            panel,
            textvariable=self.selected_provider_var,
            state="readonly",
            width=36,
        )
        self.provider_combo.grid(row=4, column=0, sticky="w", pady=(6, 14))

        ttk.Label(
            panel,
            text="当前版本只完成 API 接入选择，不会自动生成或上传笔记。",
            style="Hint.TLabel",
        ).grid(row=5, column=0, sticky="w")
        panel.columnconfigure(0, weight=1)

    def _open_api_window(self) -> None:
        ApiSettingsWindow(self, self.settings.model_providers, self._save_api_settings)

    def _save_moodle(self) -> None:
        self.settings.moodle_username = self.username_var.get().strip()
        self.settings.moodle_password = self.password_var.get()
        self.settings.remember_password = self.remember_password_var.get()
        self.settings.auto_login = self.auto_login_var.get()
        save_gui_settings(self.root_path, self.settings)
        self.status_var.set("Moodle 登录配置已保存")

    def _save_api_settings(self, providers) -> None:
        self.settings.model_providers = providers
        save_gui_settings(self.root_path, self.settings)
        self.api_status_var.set(self._api_status_text())
        self.selected_provider_var.set(self._first_connected_provider_id())
        self._refresh_note_controls()
        self.status_var.set("模型 API 配置已保存")

    def _run_check_login(self) -> None:
        self._save_moodle()
        self.status_var.set("正在检查 Moodle 登录...")
        thread = threading.Thread(target=self._check_login_worker, daemon=True)
        thread.start()

    def _check_login_worker(self) -> None:
        command = [sys.executable, "-m", "xmum_moodle_agent.cli", "check-login"]
        result = subprocess.run(command, cwd=self.root_path, capture_output=True, text=True)
        output = (result.stdout or result.stderr or "").strip()
        if result.returncode == 0:
            self.after(0, lambda: self.status_var.set(output or "Moodle 登录检查通过"))
        else:
            self.after(0, lambda: messagebox.showerror("Moodle 登录失败", output or "登录检查失败"))
            self.after(0, lambda: self.status_var.set("Moodle 登录检查失败"))

    def _refresh_note_controls(self) -> None:
        connected = [
            provider
            for provider in self.settings.model_providers
            if provider.get("enabled") and str(provider.get("api_key", "")).strip()
        ]
        values = [f"{provider['id']} - {provider['name']}" for provider in connected]
        self.provider_combo["values"] = values
        state = "normal" if can_generate_notes(self.settings) else "disabled"
        self.generate_notes_check.configure(state=state)
        self.provider_combo.configure(state="readonly" if values else "disabled")
        if not values:
            self.generate_notes_var.set(False)

    def _first_connected_provider_id(self) -> str:
        for provider in self.settings.model_providers:
            if provider.get("enabled") and str(provider.get("api_key", "")).strip():
                return f"{provider['id']} - {provider['name']}"
        return ""

    def _api_status_text(self) -> str:
        count = sum(
            1
            for provider in self.settings.model_providers
            if provider.get("enabled") and str(provider.get("api_key", "")).strip()
        )
        return f"已接入 {count} 家模型 API" if count else "尚未接入模型 API"


class ApiSettingsWindow(tk.Toplevel):
    def __init__(self, parent: MoodleAgentGui, providers, on_save):
        super().__init__(parent)
        self.parent = parent
        self.on_save = on_save
        self.provider_vars = []
        self.title("模型 API 接入")
        self.geometry("780x560")
        self.transient(parent)
        self.grab_set()

        container = ttk.Frame(self, padding=18)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="模型 API 接入", style="Title.TLabel").pack(anchor="w")
        ttk.Label(container, text="填入 API Key 并启用对应提供商后，笔记生成选项会变为可选。").pack(
            anchor="w", pady=(6, 14)
        )

        body = ttk.Frame(container)
        body.pack(fill="both", expand=True)

        canvas = tk.Canvas(body, background="#f6f7f9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        list_frame = ttk.Frame(canvas)
        list_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for index, provider in enumerate(providers):
            self._add_provider_row(list_frame, index, provider)

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(14, 0))
        ttk.Button(actions, text="保存 API 配置", style="Accent.TButton", command=self._save).pack(side="right")
        ttk.Button(actions, text="取消", command=self.destroy).pack(side="right", padx=(0, 10))

    def _add_provider_row(self, parent, index: int, provider) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        panel.grid(row=index, column=0, sticky="ew", pady=(0, 12))
        parent.columnconfigure(0, weight=1)

        enabled_var = tk.BooleanVar(value=bool(provider.get("enabled")))
        key_var = tk.StringVar(value=str(provider.get("api_key", "")))
        base_url_var = tk.StringVar(value=str(provider.get("base_url", "")))
        model_var = tk.StringVar(value=str(provider.get("model", "")))

        ttk.Checkbutton(panel, text=str(provider.get("name", "")), variable=enabled_var).grid(
            row=0, column=0, sticky="w", columnspan=2
        )
        ttk.Label(panel, text="API Key", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(panel, textvariable=key_var, show="*", width=52).grid(row=2, column=0, sticky="ew", pady=(4, 8))
        ttk.Label(panel, text="Base URL", style="Panel.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Entry(panel, textvariable=base_url_var, width=52).grid(row=4, column=0, sticky="ew", pady=(4, 8))
        ttk.Label(panel, text="默认模型", style="Panel.TLabel").grid(row=5, column=0, sticky="w")
        ttk.Entry(panel, textvariable=model_var, width=52).grid(row=6, column=0, sticky="ew", pady=(4, 0))
        panel.columnconfigure(0, weight=1)

        self.provider_vars.append(
            {
                "id": provider["id"],
                "name": provider["name"],
                "enabled": enabled_var,
                "api_key": key_var,
                "base_url": base_url_var,
                "model": model_var,
            }
        )

    def _save(self) -> None:
        providers = []
        for provider in self.provider_vars:
            providers.append(
                {
                    "id": provider["id"],
                    "name": provider["name"],
                    "enabled": provider["enabled"].get(),
                    "api_key": provider["api_key"].get().strip(),
                    "base_url": provider["base_url"].get().strip(),
                    "model": provider["model"].get().strip(),
                }
            )
        self.on_save(providers)
        self.destroy()


def main() -> int:
    app = MoodleAgentGui(Path.cwd())
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
