$ethScript = Join-Path $PSScriptRoot '\eth.ps1'
$cmsScript = Join-Path $PSScriptRoot '\cms.ps1'
. $ethScript
. $cmsScript

$script:ADDRESS_ON_DVR_LAN = "192.168.1.127"
$script:DVR_GATEWAY = "192.168.1.254"
$script:DVR_IP = "192.168.1.10"

$script:CHANGED_NETWORK = $false
$script:DHCP = $false
$script:OLD_GATEWAY = $null
$script:OLD_ADDRESS = $null
$script:CHANNELS = $null


if ($args){
    $script:CHANNELS = $args
}


function ResetStatic{
    if ($script:OLD_ADDRESS -and $script:OLD_GATEWAY){
        Set-Static -Address $script:OLD_ADDRESS -Gateway $script:OLD_GATEWAY
    }
    else
    {
        Write-Host NO OLD NETWORK SETTINGS
    }
}

function CheckNetwork
{
    $script:OLD_GATEWAY = CurrentGateway
    if (-not ($script:OLD_GATEWAY -and $script:OLD_GATEWAY -eq $script:DVR_GATEWAY))
    {
        CheckAdmin($PSCommandPath)
        Write-Host "Not on dvr network. Switching..."
        $script:DHCP = IsUsingDhcp
        $script:OLD_ADDRESS = CurrentAddress

        try
        {
            Set-Static -Address $script:ADDRESS_ON_DVR_LAN -Gateway $script:DVR_GATEWAY
            $script:CHANGED_NETWORK = $true
        }
        catch
        {
            Write-Host "caught error"
            Read-Host "Enter to Continue"
            ResetStatic
        }
    }
    if (-not (RetryReachable -ComputerName $script:DVR_IP))
    {
        Write-Host "DVR is not reachable. Exiting..."
        Read-Host "Enter to Quit"
        exit
    }

}

function mainFunc
{
    CheckNetwork
    if ($script:CHANNELS)
        {
            UILoop -Channels $script:CHANNELS
        }
        else
        {
            UILoop
        }
    if ($script:CHANGED_NETWORK)
    {
        Write-Host "Restoring network settings..."
        if ($script:DHCP)
        {
            Write-Host "Restoring DHCP..."
            Set-Dynamic
        }
        else
        {
            ResetStatic
        }
    }
#        Read-Host "Press Enter to exit..."
}


If ((Resolve-Path -Path $MyInvocation.InvocationName).ProviderPath -eq $MyInvocation.MyCommand.Path) {
    mainFunc
}
