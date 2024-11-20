$script:VIDEO_PLAYER = "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
$script:RTSP_USER = $env:RTSP_USER
$script:RTSP_PASS = $env:RTSP_PASS
$script:FRONT_CHANNELS = @(1, 2, 6, 8)
$script:FRONT_MAIN = @(1)
$script:DOOR_CHANNELS = @(2, 6)
$script:OFF_CHANNELS = @(4, 10)

function Open-Chanel([int]$Channel, [int]$Stream = 1, [string]$Codec = "H264") {
    Write-Host "Launching channel $Channel..."
    $baseUrl = "rtsp://${RTSP_USER}:${RTSP_PASS}@192.168.1.10:554"
    $url = $baseUrl + "?codec=$Codec&channel=$Channel&stream=$Stream.sdp&real_stream--rtp-caching=100"
    Start-Process -FilePath $script:VIDEO_PLAYER -ArgumentList $url
}



function UILoop([array]$channels = $null) {
    $streamQuality = 1 # 0: high quality, 1: low quality
    if (-not $channels) { $channels = $script:FRONT_MAIN }
    while ($true) {
        foreach ($chan in $channels)
        { Open-Chanel -Channel $chan -Stream $script:STREAM_QUALITY }
        $inputted = Read-Host "Choose option:
        `n`tOpen Chanels [space separated nums]
        `n`tOpen Chanel List: [d]oors [f]ront
        `n`t[r]eload viewers
        `n`t[u]pgrade quality, [y]downgrade quality,
        `n`t[Enter] tidy up and close`n"
        Stop-Process -Name "vlc" -Force -ErrorAction SilentlyContinue

        if ($inputted -ieq "r") { Write-Host "Restarting VLC..." }

        elseif ($inputted -match '^\d+(\s+\d+)*$') {
            $channels = $inputted -split "\s+"
            Write-Host "Channels updated to: $($channels -join ', ')"
        }

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
        else {
            Write-Host "Closing UI..."
            break
        }
    }
}


If ((Resolve-Path -Path $MyInvocation.InvocationName).ProviderPath -eq $MyInvocation.MyCommand.Path)
{ UILoop -Channels $args }
