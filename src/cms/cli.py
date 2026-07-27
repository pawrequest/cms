"""Rich terminal CLI for CMS."""

from __future__ import annotations

import logging
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import CMSConfig
from .channels import StreamQuality
from .config import default_config, setup_logging
from .player import CMSPlayer

console = Console()
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

QUALITY_STYLE = {
    StreamQuality.HIGH: '[bold green]HIGH[/bold green]',
    StreamQuality.LOW: '[bold yellow]LOW[/bold yellow]',
}

# Keys permanently reserved for built-in commands.
_RESERVED_KEYS: frozenset[str] = frozenset({'r', 'q'})


def _parse_channels(text: str) -> list[int]:
    """Parse a space- or comma-separated string of integers into a channel list."""
    tokens = text.replace(',', ' ').split()
    result = [int(t) for t in tokens if t.isdigit()]
    return result


def _build_group_shortcuts(config: CMSConfig) -> dict[str, str]:
    """Return a mapping of *single letter → group key* derived from the config.

    For each group the first unused letter in its name (that is not a reserved
    command key) is chosen as the shortcut.  Groups that cannot be assigned a
    unique letter are skipped with a warning.
    """
    shortcuts: dict[str, str] = {}  # letter → group key
    used: set[str] = set(_RESERVED_KEYS)

    for group_key in config.channel_groups:
        assigned = False
        for ch in group_key.lower():
            if ch.isalpha() and ch not in used:
                shortcuts[ch] = group_key
                used.add(ch)
                assigned = True
                break
        if not assigned:
            log.warning(
                'Could not assign a unique shortcut for group %r — ' 'all letters are taken or reserved.',
                group_key,
            )

    log.debug('Group shortcuts: %s', shortcuts)
    return shortcuts


def _print_status(player: CMSPlayer, group_shortcuts: dict[str, str]) -> None:
    """Render the current status panel and the help table."""
    channels_map = player.config.channels  # dict[int, str], may be empty
    if channels_map:
        channels_str = (
            ', '.join(f'{c} · {channels_map[c]}' if c in channels_map else str(c) for c in player.active_channels)
            or '[dim]none[/dim]'
        )
    else:
        channels_str = ', '.join(str(c) for c in player.active_channels) or '[dim]none[/dim]'
    quality_str = QUALITY_STYLE[player.stream_quality]

    header = Panel(
        f'  Channels : {channels_str}\n  Quality  : {quality_str}',
        title='[bold blue]CMS — Camera Management System[/bold blue]',
        border_style='blue',
        padding=(0, 2),
    )
    console.print(header)

    tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    tbl.add_column('key', style='bold cyan', min_width=12, no_wrap=True)
    tbl.add_column('action', style='white')

    # ── Dynamic group rows ────────────────────────────────────────────────
    for letter, group_key in sorted(group_shortcuts.items()):
        group_title = group_key.title()
        channels = player.config.channel_groups[group_key]
        ch_hint = ', '.join(str(c) for c in channels)
        tbl.add_row(f'\\[{letter}]', f'{group_title} channels  [dim]({ch_hint})[/dim]')

    # ── Static rows ───────────────────────────────────────────────────────
    tbl.add_row('\\[1 2 …]', 'open specific channel numbers (space or comma separated)')
    tbl.add_row('\\[r]', 'reload — close & reopen current channels')
    tbl.add_row('\\[q]', f'toggle quality from {QUALITY_STYLE[player.stream_quality]}             (reloads)')
    tbl.add_row('\\[Enter]', 'close VLC and exit')

    console.print(tbl)


# ─────────────────────────────────────────────────────────────────────────────
# UI loop (also importable for embedding)
# ─────────────────────────────────────────────────────────────────────────────


def ui_loop(player: CMSPlayer) -> None:
    """Blocking interactive loop. Exits when the user presses Enter."""
    log.debug('Entering ui_loop; active_channels=%s', player.active_channels)

    # Build shortcuts once (config does not change during a session).
    group_shortcuts = _build_group_shortcuts(player.config)

    while True:
        console.print()
        _print_status(player, group_shortcuts)

        try:
            raw = console.input('\n[bold cyan]>[/bold cyan] ').strip()
        except (EOFError, KeyboardInterrupt):
            console.print('\n[yellow]Interrupted — closing VLC.[/yellow]')
            log.debug('ui_loop interrupted — closing all')
            player.close_all()
            return

        cmd = raw.lower()
        log.debug('User command: %r', cmd)

        if cmd == '':
            player.close_all()
            console.print('[green]Closed. Goodbye![/green]')
            log.debug('User exited via Enter')
            return

        elif cmd == 'r':
            console.print('[blue]Reloading…[/blue]')
            log.debug('Reloading channels: %s', player.active_channels)
            player.reload()
            player.tiler.tile()

        elif cmd == 'q':
            player.toggle_quality()
            label = QUALITY_STYLE[player.stream_quality]
            log.debug('Quality changed to %s — reloading', player.stream_quality)
            console.print(f'Quality → {label}  — reloading…')
            player.reload()
            player.tiler.tile()

        elif cmd in group_shortcuts:
            group_key = group_shortcuts[cmd]
            group_title = group_key.title()
            log.debug('Opening group %r', group_key)
            console.print(f'[blue]Opening group [bold]{group_title}[/bold]…[/blue]')
            player.close_all()
            player.open_group(group_key)
            player.tiler.tile()

        else:
            # Try to parse as channel numbers
            nums = _parse_channels(cmd)
            if nums:
                log.debug('Opening channels: %s', nums)
                console.print(f'[blue]Opening channels: {nums}[/blue]')
                player.close_all()
                player.open_channels(nums)
                player.tiler.tile()
            else:
                log.debug('Unknown command: %r', raw)
                console.print(
                    f"[red]Unknown command '{raw}'. "
                    'Use a letter shortcut, channel numbers, or press Enter to exit.[/red]'
                )


# ─────────────────────────────────────────────────────────────────────────────
# Click entry-point
# ─────────────────────────────────────────────────────────────────────────────


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option(
    '--channels',
    '-c',
    default=None,
    metavar='1,2,6',
    help='Comma/space-separated channel numbers to open on start.',
)
@click.option(
    '--quality',
    '-q',
    type=click.Choice(['high', 'low'], case_sensitive=False),
    default='high',
    show_default=True,
    help='Initial stream quality.',
)
@click.option('--host', default=None, envvar='RTSP_HOST', help='RTSP host (overrides RTSP_HOST env var).')
@click.option('--gui', is_flag=True, default=False, help='Launch the graphical interface instead.')
@click.option(
    '--config',
    '-C',
    'config_path',
    default=None,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help='Path to a TOML config file (defaults to <project-root>/default_conf.toml). Overridden by other options where passed',
)
@click.version_option(package_name='cms')
def main(channels, quality, host, gui, config_path) -> None:
    """CMS — Camera Management System.

    Open RTSP camera feeds in VLC from the terminal or a simple GUI.

    \b
    Examples:
      cms                         # start with default group (if configured), interactive UI
      cms --channels 1,4,8        # open specific cameras
      cms --quality high          # start in high-quality mode
      cms --gui                   # launch the graphical interface
    """
    config = CMSConfig.from_toml(config_path) if config_path else default_config()
    setup_logging(config.debug)
    log.debug('Config loaded: path=%s debug=%s host=%s', config.config_toml, config.debug, config.rtsp_host)

    if quality:
        config.default_quality = StreamQuality.LOW if quality.lower().startswith('l') else StreamQuality.HIGH
        log.debug('Quality overridden to %s', config.default_quality)
    if host:
        config.rtsp_host = host
        log.debug('Host overridden to %s', host)

    if gui:
        from .gui import run_gui

        log.debug('Launching GUI mode')
        run_gui(config)
        return

    player = CMSPlayer(config)
    log.debug('CMSPlayer created; default group=%s', config.initial_group_name)

    if config.initial_group_name and config.channel_groups:
        console.print(f'[blue]Opening default group [bold]{config.initial_group_name.title()}[/bold]…[/blue]')
        player.open_group(config.initial_group_name)
        player.tiler.tile()

    elif channels:
        nums = _parse_channels(channels)
        if nums:
            log.debug('Opening channels from --channels flag: %s', nums)
            player.open_channels(nums)
            player.tiler.tile()
            console.print('[blue]Tiling…[/blue]')
        else:
            console.print('[red]No valid channel numbers in --channels.[/red]')

    ui_loop(player)
