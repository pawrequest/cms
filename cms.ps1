."E:\DOCS\Desktop\cms\eth.ps1"


$ADDRESS_ON_DVR_LAN = "192.168.1.127"
$DVR_GATEWAY = "192.168.1.254"
$DVR_IP = "192.168.1.10"

# video stuff
$VIDEO_PLAYER = "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
$RTSP_USER = $env:RTSP_USER
$RTSP_PASS = $env:RTSP_PASS
$FRONT_CHANNELS = @(1, 2, 6, 8)
$DOOR_CHANNELS = @(2, 6)
$OFF_CHANNELS = @(4, 10)
$STREAM_QUALITY = 1 # 0: high quality, 1: low quality







function Open-Chanel(
        [int]$Channel,
        [int]$Stream = $STREAM_QUALITY,
        [string]$Codec = "H264"
){
    Write-Host "Launching channel $Channel..."
    $baseUrl = "rtsp://${RTSP_USER}:${RTSP_PASS}@192.168.1.10:554"
    $url = $baseUrl + "?codec=$Codec&channel=$Channel&stream=$Stream.sdp&real_stream--rtp-caching=100"
    Start-Process -FilePath $VIDEO_PLAYER -ArgumentList $url
}


function UILoop
{
    $StreamQuality = $STREAM_QUALITY
    $channels = $FRONT_CHANNELS
    if ($args)
    {
        $channels = $args
    }
    while ($true)
    {
        foreach ($channel in $channels)
        {
            Open-Chanel -Channel $channel -Stream $StreamQuality
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
            Write-Host "Closing UI..."
            break
        }
    }
}


function mainFunc
{
    $changedNetwork = $false
    $oldAddress = CurrentAddress
    $oldGateway = CurrentGateway
    $DHCP = IsUsingDhcp

    if ($oldGateway -ne $DVR_GATEWAY)
    {
        CheckAdmin($PSCommandPath)
        Write-Host "Not on dvr network. Switching..."
        Set-Static -Address $ADDRESS_ON_DVR_LAN -Gateway $DVR_GATEWAY
        $changedNetwork = $true
    }
    if (-not (RetryReachable -ComputerName $DVR_IP))
    {
        Write-Host "DVR is not reachable.
        Exiting..."
        return
    }
    UILoop
    if ($changedNetwork)
    {
        Write-Host "Restoring network settings..."
        if ($DHCP)
        {
            Write-Host "Restoring DHCP..."
            Set-Dynamic
        }
        else
        {
            Write-Host "Restoring static..."
            Set-Static -Address $oldAddress -Gateway $oldGateway
        }
    }
#    Read-Host "Press Enter to exit..."
}

mainFunc