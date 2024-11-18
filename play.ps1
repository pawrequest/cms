function GatewayPing
{
    param (
        [string]$Gateway,
        [int]$MaxTries = 1
    )

    $pingResult = Test-Connection -ComputerName $Gateway -Count $MaxTries -Quiet

    Write-Host "Ping to $Gateway result: $pingResult"
    if ($pingResult -eq $true)
    {
        Write-Host "Gateway $Gateway is reachable."
        return $true
    }
    else
    {
        Write-Host "Gateway $Gateway is not reachable after $MaxTries attempt(s)."
        return $false
    }
}

GatewayPing 192.168.0.254 10
