import os
import subprocess
import time
import sys

# Constants
RTSP_USER = os.getenv("RTSP_USER")
RTSP_PASS = os.getenv("RTSP_PASS")
PROG_EXE = r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
DEFAULT_CHANNELS = [2, 6]


# OFFICE_ETH = ("192.168.1.127", "192.168.1.254")
# HOME_ETH = ("192.168.0.127", "192.168.0.254")


def change_ip(ip_address, gateway):
    """Run the Ethernet configuration script to change subnets."""
    # ETH_SCRIPT = r"E:\DOCS\Desktop\cms\bats\eth.bat"
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
    # change_ip(*OFFICE_ETH)
    channels = [2,6]
    launch_vlc_channels(channels)
    # time.sleep(2)
    # Get channels to launch
    # user_channels = input("Enter channels (space-separated, default: 2 6): ").strip()
    
    

    while True:
        # User prompt
        user_input = input("Enter channels (space-separated) to change, 'r' to refresh VLC windows, or [ENTER] to quit:/n ").strip().lower()
        if user_input == "r":
            close_vlc()
            print("Refreshing VLC windows...")
            launch_vlc_channels(channels)
        elif user_input.isdigit():
            channels = list(map(int, user_channels.split())) if user_channels else channels
        else:
            close_vlc()
            # print("Resetting Ethernet...")
            # change_ip(*HOME_ETH)
            sys.exit(0)


if __name__ == "__main__":
    main()
