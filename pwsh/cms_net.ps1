$ethScript = Join-Path $PSScriptRoot '\eth.ps1'
$cmsScript = Join-Path $PSScriptRoot '\cms.ps1'
. $ethScript
. $cmsScript

$script:ADDRESS_ON_DVR_LAN = "192.168.1.127"
$script:DVR_GATEWAY = "192.168.1.254"
$script:DVR_IP = "192.168.1.10"



function UseDvrNetwork($action)
{
    $oldGateway = CurrentGateway
    $oldAddress = CurrentAddress
    $wasUsingDhcp = IsUsingDhcp
    $networkChanged = $false

    try {
        if (-not ($oldGateway -and $oldGateway -eq $script:DVR_GATEWAY)) {
            CheckAdmin($PSCommandPath)
            Write-Host "Moving to DVR Network"
            Set-Static -Address $script:ADDRESS_ON_DVR_LAN -Gateway $script:DVR_GATEWAY
            $networkChanged = $true
        }
        if (-not (RetryReachable -ComputerName $script:DVR_IP)) { throw "DVR is not reachable" }

        & $action
    }
    finally {
        if ($networkChanged) {
            Write-Host "Restoring previous network settings..."
            if ($wasUsingDhcp) { Set-Dynamic }
            else { Set-Static -Address $oldAddress -Gateway $oldGateway }
#            read-host "enter to erxit"
        }
    }
}



if ((Resolve-Path -Path $MyInvocation.InvocationName).ProviderPath -eq $MyInvocation.MyCommand.Path) {
    UseDvrNetwork { UILoop -Channels $args }
}