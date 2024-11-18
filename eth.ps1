$INTERFACE_NAME = "Ethernet"
$SUBNET_MASK = "255.255.255.0"


function CurrentGateway
{
    $gateway = Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Where-Object { $_.InterfaceAlias -eq "Ethernet" }
    if ($gateway)
    {
        $res = $gateway.NextHop
        Write-Host "Current gateway: $res"
        return $res
    }
    Write-Host "No gateway found."
    return $null
}


function WaitGateway
{
    param (
        [string]$Gateway,
        [int]$MaxTries = 20
    )
    $loop_count = 1
    while ($loop_count -le $MaxTries)
    {
        $pingResult = Test-Connection -ComputerName $Gateway -Count 2 -Quiet -ErrorAction SilentlyContinue
        Write-Host "Ping to $Gateway result: $pingResult"
        if ($pingResult -eq $true)
        {
            Write-Host "Gateway $Gateway is reachable after $loop_count attempt(s)."
            return $true
        }
        else
        {
            Write-Host "Gateway $Gateway is not reachable after $loop_count attempt(s)."
            Start-Sleep -Milliseconds 500
            $loop_count++
        }
    }
    Write-Host "Gateway $Gateway was not reached after $MaxTries attempt(s)."
    return $false
}



function Set-Network
{
    param (
        [string]$Address,
        [string]$Gateway,
        [bool]$Wait = $true
    )
    Write-Host "Setting ip to $Address"
    Write-Host "Setting gateway to $Gateway"
    netsh interface ip set address name=$INTERFACE_NAME static $Address $SUBNET_MASK $Gateway
    if ($Wait)
    {
        WaitGateway -Gateway $Gateway
    }
}



function CheckAdmin(
        $scriptPath = $PSCommandPath # Script to run with priv = this one
) {
    if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator"))
    {
        Write-Host "This script requires Administrator privileges."
        $arguments = "-NoProfile -NoExit -ExecutionPolicy Bypass -File `"$scriptPath`""
        Start-Process powershell -ArgumentList $arguments -Verb RunAs
        exit
    }
}


function CheckSetEth
{
    param (
        [string]$Address,
        [string]$Gateway,
        [bool]$Wait = $true
    )
    CheckAdmin
    $currentGateway = CurrentGateway
    if ($currentGateway -ne $Gateway)
    {
        Write-Host "Setting address to $Address"
        Write-Host "Setting gateway to $Gateway"
        Set-Network -Address $Address -Gateway $Gateway -Wait $Wait
    }
    else
    {
        Write-Host "Gateway is already set to $Gateway"
    }
}

