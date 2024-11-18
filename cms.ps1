$HOME_ADDRESS = "192.168.0.27"
$HOME_GATEWAY = "192.168.0.254"
$OFFICE_ADDRESS = "192.168.1.127"
$OFFICE_GATEWAY = "192.168.1.254"

$PROG_EXE = "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
$RTSP_USER = $env:RTSP_USER
$RTSP_PASS = $env:RTSP_PASS

$FRONT_CHANNELS = @(1, 2, 6, 8)
$DOOR_CHANNELS = @(2, 6)
$OFF_CHANNELS = @(4, 10)
$DEFAULT_STREAM = 1 # 0: high quality, 1: low quality


."E:\DOCS\Desktop\cms\eth.ps1"


if (-not $args)
{
    Write-Host "No channels provided. Defaulting to front"
    $channels = $FRONT_CHANNELS
}
else
{
    $channels = $args
}

function Open-Chanel
{
    param (
        [string]$Channel,
        [int]$Stream = $DEFAULT_STREAM
    )
    $url = "rtsp://192.168.1.10:554/user=$RTSP_USER&password=$RTSP_PASS&channel=$Channel&stream=$Stream.sdp?real_stream--rtp-caching=100"
    Write-Host "Launching channel $Channel..."
    Start-Process -FilePath $PROG_EXE -ArgumentList $url
}


function UILoop
{
    $StreamQuality = $DEFAULT_STREAM
    while ($true)
    {
        foreach ($channel in $channels)
        {
            Open-Chanel -Channel $channel -Stream $StreamQuality
        }
        $inputted = Read-Host "[d]oors, [f]ront, [o]ffice, [r]efresh, [u]pgrade quality, or else reset Ethernet and close..."
        Stop-Process -Name "vlc" -Force -ErrorAction SilentlyContinue

        if ($inputted -ieq "r")
        {
            Write-Host "Restarting VLC..."
        }

        elseif ($inputted -ieq "u")
        {
            Write-Host "Upgrading Stream Quality..."
            $StreamQuality = 0
        }

        elseif ($inputted -ieq "y")
        {
            Write-Host "Downgrading Stream Quality..."
            $StreamQuality = 1
        }

        elseif ($inputted -ieq "f")
        {
            Write-Host "Switching to front channels..."
            $channels = $FRONT_CHANNELS
        }
        elseif ($inputted -ieq "d")
        {
            Write-Host "Switching to door channels..."
            $channels = $DOOR_CHANNELS
        }
        elseif ($inputted -ieq "o")
        {
            Write-Host "Switching to office channels..."
            $channels = $OFF_CHANNELS
        }

        else
        {
            Write-Host "Closing VLC and resetting Ethernet..."
            Set-Network -Address $HOME_ADDRESS -Gateway $HOME_GATEWAY -Wait $false
            exit
        }
    }
}


function mainFunc
{
    CheckAdmin($PSCommandPath)
    CheckSetEth -Address $OFFICE_ADDRESS -Gateway $OFFICE_GATEWAY -Wait $true
    UILoop
}

mainFunc
#exit