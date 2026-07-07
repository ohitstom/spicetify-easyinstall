param(
    [string]$Version,
    [string]$InstallPs1Path
)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = "SilentlyContinue"
$v = $Version
& $InstallPs1Path
