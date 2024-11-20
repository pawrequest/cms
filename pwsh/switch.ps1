."E:\DOCS\Desktop\cms\eth.ps1"

$SwitchIP = "10.90.90.90"
$SwitchSubnet = "255.0.0.0"
$SwitchGateway = "0.0.0.0"

$changedNetwork = $false
$oldAddress = CurrentAddress
$oldGateway = CurrentGateway
$oldSubnet = CurrentSubnetMask
$DHCP = IsUsingDhcp

CheckAdmin($PSCommandPath)
Set-Static -Address $SwitchIP -Gateway $SwitchGateway -SubnetMask $SwitchSubnet

Read-Host "Press Enter to exit..."

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
        Set-Static -Address $oldAddress -Gateway $oldGateway -SubnetMask $oldSubnet
        RetryReachable -ComputerName $oldGateway
    }
}