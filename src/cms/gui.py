"""Stage-2 GUI — lightweight Tkinter interface for CMS."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

from .channels import StreamQuality
from .config import CMSConfig, default_config
from .player import CMSPlayer

# ─── Catppuccin-inspired dark palette ────────────────────────────────────────
BG = '#1e1e2e'
SURFACE = '#313244'
OVERLAY = '#45475a'
TEXT = '#cdd6f4'
SUBTEXT = '#a6adc8'
BLUE = '#89b4fa'
GREEN = '#a6e3a1'
YELLOW = '#f9e2af'
RED = '#f38ba8'
MAUVE = '#cba6f7'
ACTIVE_CH_BG = '#89b4fa'
ACTIVE_CH_FG = '#1e1e2e'


def _btn(parent: tk.Widget, text: str, command, fg: str = TEXT, **kw) -> tk.Button:
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=SURFACE,
        fg=fg,
        activebackground=OVERLAY,
        activeforeground=TEXT,
        relief='flat',
        cursor='hand2',
        **kw,
    )


class CMSApp(tk.Tk):
    """Main application window."""

    def __init__(self, config: CMSConfig | None = None) -> None:
        super().__init__()
        self.title('CMS — Camera Management')
        self.configure(bg=BG)
        self.resizable(False, False)

        self.player = CMSPlayer(config)
        self._selected: set[int] = set()
        self._chan_btns: dict[int, tk.Button] = {}
        self._quality_var_i = tk.IntVar(value=self.player.stream_quality.value)

        self._build_ui()
        self.protocol('WM_DELETE_WINDOW', self._on_close)

    # ------------------------------------------------------------------ #
    # Build UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        base_font = tkfont.Font(family='Segoe UI', size=9)
        bold_font = tkfont.Font(family='Segoe UI', size=9, weight='bold')
        title_font = tkfont.Font(family='Segoe UI', size=13, weight='bold')

        # ── Title ──────────────────────────────────────────────────────
        tk.Label(
            self,
            text='CMS  Camera Viewer',
            font=title_font,
            bg=BG,
            fg=BLUE,
        ).pack(pady=(14, 2))

        # ── Status bar ─────────────────────────────────────────────────
        self._status_var = tk.StringVar(value='Ready — no channels open')
        tk.Label(
            self,
            textvariable=self._status_var,
            font=base_font,
            bg=BG,
            fg=SUBTEXT,
        ).pack(pady=(0, 10))

        # ── Group buttons ──────────────────────────────────────────────
        grp_frame = self._labeled_frame('Channel Groups')
        grp_frame.pack(padx=14, pady=(0, 6), fill='x')

        groups = [(_.title(), _) for _ in self.player.config.channel_groups]
        for col, (label, key) in enumerate(groups):
            _btn(
                grp_frame,
                label,
                command=lambda k=key: self._open_group(k),
                font=base_font,
                width=7,
            ).grid(row=0, column=col, padx=4, pady=7)

        # ── Individual channel picker ──────────────────────────────────
        ch_frame = self._labeled_frame('Channels  (click to select, then Reload)')
        ch_frame.pack(padx=14, pady=(0, 6), fill='x')

        for idx, ch in enumerate(range(1, self.player.config.max_channel + 1)):
            btn = _btn(
                ch_frame,
                str(ch),
                command=lambda c=ch: self._toggle_channel(c),
                font=base_font,
                width=4,
            )
            btn.grid(row=idx // 8, column=idx % 8, padx=3, pady=4)
            self._chan_btns[ch] = btn

        # ── Quality ────────────────────────────────────────────────────
        q_frame = tk.Frame(self, bg=BG)
        q_frame.pack(pady=(2, 6))

        tk.Label(q_frame, text='Stream quality:', bg=BG, fg=TEXT, font=base_font).pack(
            side='left', padx=(0, 8)
        )

        qual_tupes = [
            (StreamQuality.HIGH.label(), StreamQuality.HIGH.value, GREEN),
            (StreamQuality.LOW.label(), StreamQuality.LOW.value, YELLOW),
        ]
        for label, val, color in qual_tupes:
            tk.Radiobutton(
                q_frame,
                text=label,
                variable=self._quality_var_i,
                value=val,
                command=self._on_quality_change,
                bg=BG,
                fg=color,
                selectcolor=SURFACE,
                activebackground=BG,
                font=base_font,
            ).pack(side='left', padx=4)

        # ── Action buttons ─────────────────────────────────────────────
        act_frame = tk.Frame(self, bg=BG)
        act_frame.pack(pady=(4, 14))

        actions = [
            ('▶  Reload', self._open_selected, GREEN),
            ('✕  Close All', self._close_all, RED),
        ]
        for text, cmd, color in actions:
            _btn(act_frame, text, command=cmd, fg=color, font=bold_font, width=16).pack(
                side='left', padx=6
            )

        # ── Settings (collapsible) ─────────────────────────────────────
        self._build_settings()

    def _labeled_frame(self, label: str) -> tk.LabelFrame:
        outer = tk.LabelFrame(
            self,
            text=f'  {label}  ',
            bg=BG,
            fg=BLUE,
            font=tkfont.Font(family='Segoe UI', size=8, weight='bold'),
            relief='groove',
            bd=1,
        )
        return outer

    def _build_settings(self) -> None:
        """Collapsible settings panel for host and credentials."""
        self._settings_visible = False
        toggle_btn = tk.Button(
            self,
            text='⚙  Settings ▾',
            command=self._toggle_settings,
            bg=BG,
            fg=SUBTEXT,
            activebackground=BG,
            relief='flat',
            cursor='hand2',
            font=tkfont.Font(family='Segoe UI', size=8),
        )
        toggle_btn.pack(anchor='center', pady=(0, 4))

        self._settings_frame = tk.Frame(self, bg=BG)
        small = tkfont.Font(family='Segoe UI', size=9)

        def _label(text: str, row: int) -> None:
            tk.Label(
                self._settings_frame,
                text=text,
                bg=BG,
                fg=SUBTEXT,
                font=small,
                width=10,
                anchor='e',
            ).grid(row=row, column=0, padx=(8, 4), pady=3)

        def _entry(var: tk.StringVar, row: int, **kw) -> tk.Entry:
            e = tk.Entry(
                self._settings_frame,
                textvariable=var,
                width=24,
                bg=SURFACE,
                fg=TEXT,
                insertbackground=TEXT,
                relief='flat',
                font=small,
                **kw,
            )
            e.grid(row=row, column=1, padx=(0, 8), pady=3)
            return e

        # ── Config file (click for context menu) ─────────────────────
        _label('Config file:', 0)
        cfg_path = self.player.config.path
        cfg_name = cfg_path.name if cfg_path else '—'
        self._cfg_lbl = tk.Label(
            self._settings_frame,
            text=cfg_name,
            bg=BG,
            fg=BLUE,
            font=small,
            anchor='w',
            cursor='hand2',
        )
        self._cfg_lbl.grid(row=0, column=1, padx=(0, 8), pady=3, sticky='w')
        self._cfg_lbl.bind('<Button-1>', self._show_config_menu)

        # ── Host ──────────────────────────────────────────────────────
        _label('Host:', 1)
        self._host_var = tk.StringVar(value=self.player.config.rtsp_host)
        _entry(self._host_var, 1)

        # ── Username ──────────────────────────────────────────────────
        _label('Username:', 2)
        self._user_var = tk.StringVar(value=self.player.config.rtsp_user or '')
        _entry(self._user_var, 2)

        # ── Password ──────────────────────────────────────────────────
        _label('Password:', 3)
        self._pass_var = tk.StringVar(value=self.player.config.rtsp_pass or '')
        _entry(self._pass_var, 3, show='•')

        # ── Hint ──────────────────────────────────────────────────────
        tk.Label(
            self._settings_frame,
            text='Leave username/password blank to keep existing credentials.',
            bg=BG,
            fg=OVERLAY,
            font=tkfont.Font(family='Segoe UI', size=8, slant='italic'),
            wraplength=240,
        ).grid(row=4, column=0, columnspan=2, padx=8, pady=(0, 2))

        # ── Buttons row ───────────────────────────────────────────────
        btn_row = tk.Frame(self._settings_frame, bg=BG)
        btn_row.grid(row=5, column=0, columnspan=2, pady=(4, 8))

        tk.Button(
            btn_row,
            text='Apply',
            command=self._apply_settings,
            bg=MAUVE,
            fg=BG,
            activebackground=OVERLAY,
            relief='flat',
            cursor='hand2',
            font=tkfont.Font(family='Segoe UI', size=9, weight='bold'),
            width=8,
        ).pack(side='left', padx=(0, 6))

        tk.Button(
            btn_row,
            text='↺  From env',
            command=self._reload_creds_from_env,
            bg=SURFACE,
            fg=SUBTEXT,
            activebackground=OVERLAY,
            activeforeground=TEXT,
            relief='flat',
            cursor='hand2',
            font=tkfont.Font(family='Segoe UI', size=9),
            width=10,
        ).pack(side='left')

    # ------------------------------------------------------------------ #
    # Interactivity
    # ------------------------------------------------------------------ #

    def _toggle_settings(self) -> None:
        if self._settings_visible:
            self._settings_frame.pack_forget()
        else:
            self._settings_frame.pack(pady=(0, 10))
        self._settings_visible = not self._settings_visible

    def _apply_settings(self) -> None:
        self.player.config.rtsp_host = self._host_var.get().strip()
        # Only overwrite credentials if the user actually typed something.
        user = self._user_var.get().strip()
        if user:
            self.player.config.rtsp_user = user
        passwd = self._pass_var.get()
        if passwd:
            self.player.config.rtsp_pass = passwd
        self._set_status('Settings applied.')

    def _reload_creds_from_env(self) -> None:
        """Pull RTSP_USER / RTSP_PASS from environment and refresh fields + config."""
        import os
        user = os.getenv('RTSP_USER', '')
        passwd = os.getenv('RTSP_PASS', '')
        self._user_var.set(user)
        self._pass_var.set(passwd)
        self.player.config.rtsp_user = user or self.player.config.rtsp_user
        self.player.config.rtsp_pass = passwd or self.player.config.rtsp_pass
        self._set_status('Credentials reloaded from environment.')

    # ── Config-file context menu ───────────────────────────────────────

    def _show_config_menu(self, event: tk.Event) -> None:
        """Pop up a small context menu on the config filename label."""
        menu = tk.Menu(
            self, tearoff=0, bg=SURFACE, fg=TEXT,
            activebackground=OVERLAY, activeforeground=TEXT,
            relief='flat', bd=0
        )
        cfg_path = self.player.config.path
        menu.add_command(
            label='Open file',
            state='normal' if cfg_path else 'disabled',
            command=self._cfg_open_file,
        )
        menu.add_command(
            label='Open path',
            state='normal' if cfg_path else 'disabled',
            command=self._cfg_open_path,
        )
        menu.add_separator()
        menu.add_command(label='Replace…', command=self._cfg_replace)
        menu.tk_popup(event.x_root, event.y_root)

    def _cfg_open_file(self) -> None:
        """Open the config TOML in the system default text editor."""
        import os
        path = self.player.config.path
        if path:
            os.startfile(str(path))

    def _cfg_open_path(self) -> None:
        """Reveal the config file's parent directory in Windows Explorer."""
        import subprocess
        path = self.player.config.path
        if path:
            subprocess.Popen(['explorer', str(path.parent)])

    def _cfg_replace(self) -> None:
        """Let the user pick a new TOML file and hot-reload the config."""
        from tkinter import filedialog
        from .config import CMSConfig
        current = self.player.config.path
        initial_dir = str(current.parent) if current else '/'
        new_path_str = filedialog.askopenfilename(
            parent=self,
            title='Select config TOML',
            initialdir=initial_dir,
            filetypes=[('TOML files', '*.toml'), ('All files', '*.*')],
        )
        if not new_path_str:
            return  # user cancelled
        from pathlib import Path
        new_path = Path(new_path_str)
        try:
            new_cfg = CMSConfig.from_toml(new_path)
        except Exception as exc:
            self._set_status(f'Failed to load config: {exc}')
            return
        self.player.config = new_cfg
        # Refresh settings fields
        self._cfg_lbl.configure(text=new_path.name)
        self._host_var.set(new_cfg.rtsp_host or '')
        self._user_var.set(new_cfg.rtsp_user or '')
        self._pass_var.set(new_cfg.rtsp_pass or '')
        self._set_status(f'Config replaced: {new_path.name}')

    def _set_status(self, msg: str) -> None:
        self._status_var.set(msg)

    def _highlight_channels(self, channels: list[int]) -> None:
        """Visually mark *channels* as active, clear all others."""
        for ch, btn in self._chan_btns.items():
            if ch in channels:
                btn.configure(bg=ACTIVE_CH_BG, fg=ACTIVE_CH_FG)
            else:
                btn.configure(bg=SURFACE, fg=TEXT)
        self._selected = set(channels)

    def _toggle_channel(self, ch: int) -> None:
        if ch in self._selected:
            self._selected.discard(ch)
            self._chan_btns[ch].configure(bg=SURFACE, fg=TEXT)
        else:
            self._selected.add(ch)
            self._chan_btns[ch].configure(bg=ACTIVE_CH_BG, fg=ACTIVE_CH_FG)

    def _on_quality_change(self) -> None:
        """Sync radio button → player quality, then reload if streams are open."""
        # self.player.toggle_quality()
        self.player.set_quality(StreamQuality(self._quality_var_i.get()))
        if self.player.active_channels:
            self._launch(self.player.active_channels)

    # ── Channel actions ────────────────────────────────────────────────

    def _launch(self, channels: list[int]) -> None:
        """Close existing streams, open *channels* at current quality, then tile."""
        if not channels:
            self._set_status('No channels to open.')
            return
        self.player.close_all()
        self.player.open_and_tile_channels(channels)
        self._highlight_channels(channels)
        self._set_status(f'Opened channels: {channels} — tiling…')

    def _open_group(self, group: str) -> None:
        self._launch(self.player.config.channel_groups[group])

    def _open_selected(self) -> None:
        if not self._selected:
            self._set_status('No channels selected — click channel numbers first.')
            return
        self._launch(sorted(self._selected))

    def _reload(self) -> None:
        """Re-open whatever channels are currently active (or selected)."""
        active = self.player.active_channels or sorted(self._selected)
        self._launch(active)

    def _close_all(self) -> None:
        self.player.close_all()
        self._set_status('All streams closed.')

    def _on_close(self) -> None:
        self.player.close_all()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────


def run_gui(config: CMSConfig | None = None) -> None:
    """Launch the CMS GUI (blocks until the window is closed).

    When the interpreter lives inside a venv the Tcl/Tk shared libraries are
    located under the *base* Python prefix, not the venv prefix.  We set
    TCL_LIBRARY / TK_LIBRARY from ``sys.base_prefix`` before Tk() is
    constructed so the correct ``init.tcl`` is found automatically.
    """
    import os
    import sys

    base = sys.base_prefix
    for env_var, subdir in [('TCL_LIBRARY', 'tcl8.6'), ('TK_LIBRARY', 'tk8.6')]:
        if env_var not in os.environ:
            candidate = os.path.join(base, 'tcl', subdir)
            if os.path.isdir(candidate):
                os.environ[env_var] = candidate

    config = config or default_config()
    app = CMSApp(config)
    app.mainloop()


if __name__ == '__main__':
    run_gui()
