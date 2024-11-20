$INTERFACE_NAME = "Ethernet"
$SUBNET_MASK = "255.255.255.0"
$DNS1 = "8.8.8.8"
$DNS2 = "1.1.2.2"

function CurrentGateway {
    return (Get-NetRoute -DestinationPrefix "0.0.0.0/0" |
            Where-Object { $_.InterfaceAlias -eq $INTERFACE_NAME }).NextHop
}

function CurrentAddress {
    return (Get-NetIPAddress -InterfaceAlias $INTERFACE_NAME |
            Where-Object { $_.AddressFamily -eq "IPv4" }).IPAddress
}

function CurrentSubnetMask {
    return Get-WmiObject Win32_NetworkAdapterConfiguration | Where IPEnabled |  Select-Object -First 1 |
           Select -ExpandProperty IPSubnet | Select-Object -First 1
}

function CW {
    Get-WmiObject Win32_NetworkAdapterConfiguration -InterfaceAlias $INTERFACE_NAME
}

function IsReachable([string]$ComputerName, [int]$PingCount = 1) {
    $reachres = Test-Connection -ComputerName $ComputerName -Count $PingCount -Quiet -ErrorAction SilentlyContinue
    if ($reachres -eq $true) { Write-Host "$ComputerName is reachable" }
    else { Write-Host "$ComputerName is NOT reachable" }
    return $reachres
}


function RetryReachable([string]$ComputerName, [int]$MaxTries = 20) {
    for ($i = 1; $i -lt $MaxTries; $i++) {
        if ((IsReachable -ComputerName $ComputerName) -eq $true) {
            write-host "$ComputerName is reachable after $i attempt(s)."
            return $true
        }
        else {
            Start-Sleep -Milliseconds 500
            $loop_count++
        }
    }
    Write-Error "$ComputerName was not reached after $i attempt(s)."
    return $false
}




function Set-Static(
        [string]$Address,
        [string]$Gateway,
        [string]$SubnetMask = $SUBNET_MASK,
        [string]$Dns1 = $DNS1,
        [string]$Dns2 = $DNS2
)
{
    netsh interface ip set dns name=$INTERFACE_NAME static address=$Dns1
    #    netsh interface ip set dns name=$INTERFACE_NAME static address=$Dns2
    netsh interface ip set address name=$INTERFACE_NAME source=static address=$Address $SUBNET_MASK $Gateway
    Write-Host "network updated: Address=$Address, Gateway=$Gateway, DNS1=$Dns1"
}

function IsUsingDhcp()
{
    $adapterConfig = Get-NetIPConfiguration -InterfaceAlias $INTERFACE_NAME -Detailed
    $res = $adapterConfig.NetIPv4Interface.DHCP
    return ($res -eq "Enabled")
}


function Set-Dynamic()
{
    Write-Host "Setting IP to dynamic"
    netsh interface ip set dns name=$INTERFACE_NAME source=dhcp
    netsh interface ip set address name=$INTERFACE_NAME source=dhcp

}


function CheckAdmin(
        $scriptPath = $PSCommandPath # Script to run with priv = this one
)
{
    if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator"))
    {
        Write-Host "Restarting with Administrator privileges."
        $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
        Start-Process powershell -ArgumentList $arguments -Verb RunAs
        exit
    }
}


