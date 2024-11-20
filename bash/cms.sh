#!/bin/bash

# Set the video player path (adjust for Linux VLC path)
VIDEO_PLAYER="/usr/bin/vlc"

# Get RTSP credentials from environment variables
RTSP_USER=$RTSP_USER
RTSP_PASS=$RTSP_PASS

# Define channel lists
FRONT_CHANNELS=(1 2 6 8)
FRONT_MAIN=(1)
DOOR_CHANNELS=(2 6)
OFF_CHANNELS=(4 10)

# Default stream quality (1: low, 0: high)
STREAM_QUALITY=1

# Function to open channel using VLC
Open-Chanel() {
    local Channel=$1
    local Stream=${2:-1} # Default to stream 1 if not specified
    local Codec=${3:-"H264"} # Default to H264 codec if not specified

    echo "Launching channel $Channel..."
    local baseUrl="rtsp://$RTSP_USER:$RTSP_PASS@192.168.1.10:554"
    local url="${baseUrl}?codec=$Codec&channel=$Channel&stream=$Stream.sdp&real_stream--rtp-caching=100"

    # Launch VLC with the URL
    $VIDEO_PLAYER "$url" &
}

# Function to run the UI loop
UILoop() {
    local channels=("${@:-${FRONT_MAIN[@]}}") # Default to FRONT_MAIN if no channels are passed

    while true; do
        # Open all channels
        for chan in "${channels[@]}"; do
            Open-Chanel "$chan" "$STREAM_QUALITY"
        done

        # Prompt for user input
        echo -e "\nChoose option:"
        echo -e "\tOpen Channels (space-separated numbers)"
        echo -e "\tOpen Channel List: [d]oors [f]ront"
        echo -e "\t[r]eload viewers"
        echo -e "\t[u]pgrade quality, [y]downgrade quality"
        echo -e "\t[Enter] tidy up and close"

        read -p "Enter choice: " inputted

        # Close VLC if running
        pkill -f "vlc" 2>/dev/null

        if [[ "$inputted" == "r" ]]; then
            echo "Restarting VLC..."
#        elif [[ "$inputted" =~ ^[0-9]+(\s+[0-9]+)*$ ]]; then
#            # Update channels from user input (space-separated numbers)
#            IFS=' ' read -r -a channels <<< "$inputted"
#            echo "Channels updated to: ${channels[@]}"
        elif [[ "$inputted" == "u" ]]; then
            echo "Upgrading Stream Quality..."
            STREAM_QUALITY=0
        elif [[ "$inputted" == "y" ]]; then
            echo "Downgrading Stream Quality..."
            STREAM_QUALITY=1
        elif [[ "$inputted" == "f" ]]; then
            echo "Switching to front channels..."
            channels=("${FRONT_CHANNELS[@]}")
        elif [[ "$inputted" == "d" ]]; then
            echo "Switching to door channels..."
            channels=("${DOOR_CHANNELS[@]}")
        elif [[ "$inputted" == "o" ]]; then
            echo "Switching to office channels..."
            channels=("${OFF_CHANNELS[@]}")
        else
            echo "Closing UI..."
            break
        fi
    done
}

# If running as a script, start the UI loop with provided arguments
if [[ "$(basename "$0")" == "$(basename "$BASH_SOURCE")" ]]; then
    UILoop "$@"
fi
