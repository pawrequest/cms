$INTERFACE_NAME = "Ethernet"

function Get-NetworkConfig {
    $adapt = Get-WmiObject Win32_NetworkAdapterConfiguration | Where IPEnabled |  Select-Object -First 1 |
             Select -ExpandProperty IPSubnet | Select-Object -First 1
    $adapter = Get-WmiObject Win32_NetworkAdapterConfiguration |
               Where-Object { $_.Description -eq $INTERFACE_NAME -and $_.IPEnabled }

    if (-not $adapter) {
        Write-Error "No adapter found for the specified interface name: $INTERFACE_NAME"
        return $null
    }
    return $adapter
}

function Set-NetworkConfig($adapter) {
    if (-not $adapter) {
        Write-Error "Invalid network adapter object passed."
        return
    }

    if ($adapter.DHCPEnabled) {
        $adapter.EnableDHCP() | Out-Null
        $adapter.SetDNSServerSearchOrder($null) | Out-Null  # Reset DNS to automatic
        Write-Host "Configuration restored to DHCP."
    } else {
        $adapter.EnableStatic($adapter.IPAddress, $adapter.IPSubnet) | Out-Null
        $adapter.SetGateways($adapter.DefaultIPGateway) | Out-Null
        $adapter.SetDNSServerSearchOrder($adapter.DNSServerSearchOrder) | Out-Null
        Write-Host "Static configuration restored."
    }
}

## Usage Example
#$config = Get-NetworkConfig
#Set-NetworkConfig -adapter $config


function Get-SomeNets($InterfaceName = "Ethernet") {
    return Get-NetAdapter -Name $INTERFACE_NAME |
    Where-Object { $_.Status -eq "Up" } |
    Select-Object -First 1 |
    ForEach-Object {
        $ipConfig = Get-NetIPAddress -InterfaceAlias $_.Name -AddressFamily IPv4
        $route = Get-NetRoute -DestinationPrefix "0.0.0.0/0" -InterfaceAlias $_.Name
        [pscustomobject]@{
            InterfaceAlias = $_.Name
            Address = $ipConfig.IPAddress
            SubnetMask = $ipConfig.PrefixLength
            Gateway = $route.NextHop
        }
    }
}

#Get-SomeNets