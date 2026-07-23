"""Stage-2 GUI — lightweight Tkinter interface for CMS."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

from .channels import StreamQuality
from .config import CMSConfig, MAX_CHANNEL, CHANNEL_GROUPS
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

        self.player = CMSPlayer(config or CMSConfig())
        self._selected: set[int] = set()
        self._chan_btns: dict[int, tk.Button] = {}

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

        groups = [
            ('Doors', 'doors'),
            ('Front', 'front'),
            ('Main', 'main'),
            ('Office', 'office'),
            ('All', 'all'),
        ]
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

        for idx, ch in enumerate(range(1, MAX_CHANNEL + 1)):
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

        # self._quality_var = tk.StringVar(value="qual")
        self._quality_var_i = tk.IntVar(value=self.player.stream_quality.value)
        qual_tupes = [
            (StreamQuality.HIGH.label().title(), StreamQuality.HIGH.value, GREEN),
            (StreamQuality.LOW.label().title(), StreamQuality.LOW.value, YELLOW),
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

        # q_frame.update()

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
        """Collapsible settings panel.

        Credentials (RTSP_USER / RTSP_PASS) are intentionally read-only from
        the environment — set them via ``$env:RTSP_USER`` / ``$env:RTSP_PASS``
        before launching, matching the cms.ps1 behaviour.
        Only the host address is editable here.
        """
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

        # ── Host (editable) ───────────────────────────────────────────
        tk.Label(
            self._settings_frame,
            text='Host:',
            bg=BG,
            fg=SUBTEXT,
            font=small,
            width=10,
            anchor='e',
        ).grid(row=0, column=0, padx=(8, 4), pady=3)

        self._host_var = tk.StringVar(value=self.player.config.rtsp_host)
        tk.Entry(
            self._settings_frame,
            textvariable=self._host_var,
            width=24,
            bg=SURFACE,
            fg=TEXT,
            insertbackground=TEXT,
            relief='flat',
            font=small,
        ).grid(row=0, column=1, padx=(0, 8), pady=3)

        # ── Credentials (read-only, sourced from env) ─────────────────
        env_note = 'Credentials are read from RTSP_USER / RTSP_PASS env vars.'
        tk.Label(
            self._settings_frame,
            text=env_note,
            bg=BG,
            fg=SUBTEXT,
            font=tkfont.Font(family='Segoe UI', size=8, slant='italic'),
            wraplength=240,
        ).grid(row=1, column=0, columnspan=2, padx=8, pady=(2, 4))

        tk.Button(
            self._settings_frame,
            text='Apply',
            command=self._apply_settings,
            bg=MAUVE,
            fg=BG,
            activebackground=OVERLAY,
            relief='flat',
            cursor='hand2',
            font=tkfont.Font(family='Segoe UI', size=9, weight='bold'),
            width=8,
        ).grid(row=2, column=0, columnspan=2, pady=(4, 8))

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
        self._set_status('Settings applied.')

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
        self.player.toggle_quality()
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
        self._launch(CHANNEL_GROUPS[group])

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

    app = CMSApp(config)
    app.mainloop()


if __name__ == '__main__':
    run_gui()
