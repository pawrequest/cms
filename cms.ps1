$script:VIDEO_PLAYER = "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
$script:RTSP_USER = $env:RTSP_USER
$script:RTSP_PASS = $env:RTSP_PASS
$script:FRONT_CHANNELS = @(1, 2, 6, 8)
$script:FRONT_MAIN = @(1)
$script:DOOR_CHANNELS = @(2, 6)
$script:OFF_CHANNELS = @(4, 10)
$script:STREAM_QUALITY = 1 # 0: high quality, 1: low quality

function Open-Chanel(
        [int]$Channel,
        [int]$Stream = $STREAM_QUALITY,
        [string]$Codec = "H264"
)
{
    Write-Host "Launching channel $Channel..."
    $baseUrl = "rtsp://${RTSP_USER}:${RTSP_PASS}@192.168.1.10:554"
    $url = $baseUrl + "?codec=$Codec&channel=$Channel&stream=$Stream.sdp&real_stream--rtp-caching=100"
    Start-Process -FilePath $script:VIDEO_PLAYER -ArgumentList $url
}


function UILoop($Channels = $script:FRONT_MAIN)
{
    while ($true)
    {
        foreach ($channel in $Channels)
        {
            Open-Chanel -Channel $channel -Stream $script:STREAM_QUALITY
        }
        $inputted = Read-Host "[d]oors, [f]ront, [o]ffice, [r]efresh, [u]pgrade quality, [y]downgrade quality, or else tidy up and close..."
        Stop-Process -Name "vlc" -Force -ErrorAction SilentlyContinue

        if ($inputted -ieq "r")
        {
            Write-Host "Restarting VLC..."
        }

        elseif ($inputted -ieq "u")
        {
            Write-Host "Upgrading Stream Quality..."
            $script:STREAM_QUALITY = 0
        }

        elseif ($inputted -ieq "y")
        {
            Write-Host "Downgrading Stream Quality..."
            $script:STREAM_QUALITY = 1
        }

        elseif ($inputted -ieq "f")
        {
            Write-Host "Switching to front channels..."
            $Channels = $FRONT_CHANNELS
        }
        elseif ($inputted -ieq "d")
        {
            Write-Host "Switching to door channels..."
            $Channels = $DOOR_CHANNELS
        }
        elseif ($inputted -ieq "o")
        {
            Write-Host "Switching to office channels..."
            $Channels = $OFF_CHANNELS
        }

        else
        {
            Write-Host "Closing UI..."
            break
        }
    }
}


If ((Resolve-Path -Path $MyInvocation.InvocationName).ProviderPath -eq $MyInvocation.MyCommand.Path)
{
    if ($args)
    {
        UILoop -Channels $args
    }
    else
    {
        UILoop
    }
}
