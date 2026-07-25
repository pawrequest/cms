"""Rich terminal CLI for CMS."""

from __future__ import annotations

import sys

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .channels import StreamQuality
from .config import default_config
from .player import CMSPlayer

console = Console()

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

QUALITY_STYLE = {
    StreamQuality.HIGH: '[bold green]HIGH[/bold green]',
    StreamQuality.LOW: '[bold yellow]LOW[/bold yellow]',
}

GROUP_SHORTCUTS: dict[str, str] = {
    'd': 'doors',
    'f': 'front',
    'm': 'main',
    'o': 'office',
    'a': 'all',
}


def _parse_channels(text: str) -> list[int]:
    """Parse a space- or comma-separated string of integers into a channel list."""
    tokens = text.replace(',', ' ').split()
    result = [int(t) for t in tokens if t.isdigit()]
    return result


def _print_status(player: CMSPlayer) -> None:
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
    rows = [
        ('[d]', 'doors channels'),
        ('[f]', 'front channels'),
        ('[m]', 'main channel'),
        ('[o]', 'office channels'),
        ('[a]', 'all channels'),
        ('[1 2 …]', 'open specific channel numbers (space or comma separated)'),
        ('[r]', 'reload — close & reopen current channels'),
        # ("[w]",      "tile VLC windows into a grid"),
        ('[u]', 'upgrade to HIGH quality stream  (reloads)'),
        ('[y]', 'downgrade to LOW  quality stream (reloads)'),
        ('[t]', 'toggle quality                  (reloads)'),
        ('[Enter]', 'close VLC and exit'),
    ]
    for key, action in rows:
        tbl.add_row(key, action)
    console.print(tbl)


# ─────────────────────────────────────────────────────────────────────────────
# UI loop (also importable for embedding)
# ─────────────────────────────────────────────────────────────────────────────


def ui_loop(player: CMSPlayer) -> None:
    """Blocking interactive loop. Exits when the user presses Enter."""
    while True:
        console.print()
        _print_status(player)

        try:
            raw = console.input('\n[bold cyan]>[/bold cyan] ').strip()
        except (EOFError, KeyboardInterrupt):
            console.print('\n[yellow]Interrupted — closing VLC.[/yellow]')
            player.close_all()
            return

        cmd = raw.lower()

        if cmd == '':
            player.close_all()
            console.print('[green]Closed. Goodbye![/green]')
            return

        elif cmd == 'r':
            console.print('[blue]Reloading…[/blue]')
            player.reload()

        # elif cmd == "w":
        #     console.print("[blue]Tiling windows…[/blue]")
        #     ok = player.tile_windows()
        #     if not ok:
        #         console.print("[yellow]No VLC windows found to tile.[/yellow]")

        elif cmd in ('u', 'y', 't'):
            if cmd == 'u':
                player.upgrade_quality()
            elif cmd == 'y':
                player.downgrade_quality()
            else:
                player.toggle_quality()
            label = QUALITY_STYLE[player.stream_quality]
            console.print(f'Quality → {label}  — reloading…')
            player.reload()

        elif cmd in GROUP_SHORTCUTS:
            group = GROUP_SHORTCUTS[cmd]
            console.print(f'[blue]Opening group [bold]{group}[/bold]…[/blue]')
            player.close_all()
            player.open_group(group)

        else:
            # Try to parse as channel numbers
            nums = _parse_channels(cmd)
            if nums:
                console.print(f'[blue]Opening channels: {nums}[/blue]')
                player.close_all()
                player.open_and_tile_channels(nums)
            else:
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
@click.option(
    '--host', default=None, envvar='RTSP_HOST', help='RTSP host (overrides RTSP_HOST env var).'
)
@click.option('--gui', is_flag=True, default=False, help='Launch the graphical interface instead.')
@click.version_option(package_name='cms')
def main(channels, quality, host, gui) -> None:
    """CMS — Camera Management System.

    Open RTSP camera feeds in VLC from the terminal or a simple GUI.

    variables (set them before launching, as with cms.ps1).

    \b
    Examples:
      cms                         # start with default group (doors), interactive UI
      cms --channels 1,4,8        # open specific cameras
      cms --quality high          # start in high-quality mode
      cms --gui                   # launch the graphical interface
    """
    if gui:
        from .gui import run_gui

        run_gui()
        return

    config = default_config()
    if quality:
        config.default_quality = (
            StreamQuality.LOW if quality.lower().startswith('l') else StreamQuality.HIGH
        )
    if host:
        config.rtsp_host = host

    player = CMSPlayer(config)

    if channels:
        nums = _parse_channels(channels)
        if not nums:
            console.print('[red]No valid channel numbers in --channels.[/red]')
            sys.exit(1)
        player.open_and_tile_channels(nums)
        console.print('[blue]Tiling…[/blue]')

    ui_loop(player)
