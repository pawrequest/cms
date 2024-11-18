import os
import subprocess

# Constants
RTSP_USER = os.getenv("RTSP_USER")
RTSP_PASS = os.getenv("RTSP_PASS")
PROG_EXE = r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
DEFAULT_CHANNELS = [2, 6]
ETH_SCRIPT = r"E:\DOCS\Desktop\cms\gen_eth.bat"

OFFICE_ETH = ("192.168.1.127", "192.168.1.254")
HOME_ETH = ("192.168.0.127", "192.168.0.254")


def change_ip(ip_address, gateway):
    """Run the Ethernet configuration script."""
    subprocess.run(
        [
            "powershell",
            "-Command",
            f'Start-Process cmd.exe -ArgumentList "/c, {ETH_SCRIPT} {ip_address} {gateway}" -Verb RunAs -Wait',
        ],
        check=True,
    )


def launch_vlc_channels(channels):
    """Launch VLC instances for given channels."""
    for chan in channels:
        url = f"rtsp://192.168.1.10:554/user={RTSP_USER}&password={RTSP_PASS}&channel={chan}&stream=0.sdp?real_stream--rtp-caching=100"
        print(f"Launching channel {chan}...")
        subprocess.Popen([PROG_EXE, url])


def close_vlc():
    """Close all VLC processes."""
    subprocess.run(["taskkill", "/IM", "vlc.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    change_ip(*OFFICE_ETH)

    # Get channels to launch
    user_channels = input("Enter channels (space-separated, default: 2 6): ").strip()
    channels = list(map(int, user_channels.split())) if user_channels else DEFAULT_CHANNELS
    launch_vlc_channels(channels)

    while True:
        # User prompt
        user_input = input("Press 'r' to refresh VLC windows, or 'q' to reset eth and quit: ").strip().lower()
        if user_input == "r":
            close_vlc()
            print("Refreshing VLC windows...")
            launch_vlc_channels(channels)
        else:
            close_vlc()
            print("Resetting Ethernet...")
            change_ip(*HOME_ETH)


if __name__ == "__main__":
    main()
