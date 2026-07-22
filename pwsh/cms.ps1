$script:VIDEO_PLAYER = "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
$script:RTSP_USER = $env:RTSP_USER
$script:RTSP_PASS = $env:RTSP_PASS
$script:RTSP_IP = $env:RTSP_IP
$script:FRONT_CHANNELS = @(1, 2, 6, 8)
$script:FRONT_MAIN = @(1)
$script:DOOR_CHANNELS = @(2, 6)
$script:OFF_CHANNELS = @(4, 10)
$script:ALL_CHANNELS = @(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)

function Open-Chanel([int]$Channel, [int]$Stream = 1, [string]$Codec = "H264") {
    Write-Host "Launching channel $Channel..."
    $baseUrl = "rtsp://${RTSP_USER}:${RTSP_PASS}@192.168.1.${RTSP_IP}:554"
    $url = $baseUrl + "?codec=$Codec&channel=$Channel&stream=$Stream.sdp&real_stream--rtp-caching=100"
    Start-Process -FilePath $script:VIDEO_PLAYER -ArgumentList $url
}


function UILoop([array]$channels = $null) {
    $streamQuality = 1 # 0: high quality, 1: low quality
    if (-not $channels) { $channels = $script:FRONT_CHANNELS }
    while ($true) {
        foreach ($chan in $channels)
        { Open-Chanel -Channel $chan -Stream $script:STREAM_QUALITY }
        $inputted = Read-Host "Choose option:
        `n`t[d]oors [f]ront [o]ffice [a]ll (change channels)
        `n`t[r]eload viewers
        `n`t[u]pgrade quality, [y]downgrade quality,
        `n`t[Enter] tidy up and close`n"
        Stop-Process -Name "vlc" -Force -ErrorAction SilentlyContinue

        if ($inputted -ieq "r") { Write-Host "Restarting VLC..." }

        elseif ($inputted -ieq "u") {
            Write-Host "Upgrading Stream Quality..."
            $script:STREAM_QUALITY = 0
        }
        elseif ($inputted -ieq "y") {
            Write-Host "Downgrading Stream Quality..."
            $script:STREAM_QUALITY = 1
        }
        elseif ($inputted -ieq "f") {
            Write-Host "Switching to front channels..."
            $channels = $FRONT_CHANNELS
        }
        elseif ($inputted -ieq "d") {
            Write-Host "Switching to door channels..."
            $channels = $DOOR_CHANNELS
        }
        elseif ($inputted -ieq "o") {
            Write-Host "Switching to office channels..."
            $channels = $OFF_CHANNELS
        }
        elseif ($inputted -ieq "a") {
            Write-Host "Switching to all channels..."
            $channels = $ALL_CHANNELS
        }
        else {
            Write-Host "Closing UI..."
            break
        }
    }
}


If ((Resolve-Path -Path $MyInvocation.InvocationName).ProviderPath -eq $MyInvocation.MyCommand.Path) {
    UILoop -Channels $args
}
