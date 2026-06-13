# patch_hosts.ps1
# Requires Administrator privileges to modify the hosts file.

$HostsPath = "$env:windir\System32\drivers\etc\hosts"
$Entry = "127.0.0.1 upgrade.scdn.co"
$Comment = "# Spicetify-Easyinstall Legacy Fix"

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host "This script requires Administrator privileges. Relaunching as Admin..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# Present Menu
Write-Host "============================================="
Write-Host "   Spicetify Legacy Hosts Patcher"
Write-Host "============================================="
Write-Host "1) Enable Patch (Redirect upgrade.scdn.co to localhost)"
Write-Host "2) Disable Patch (Restore default behavior)"
Write-Host "3) Exit"
Write-Host ""
$choice = Read-Host "Select an option [1-3]"

if ($choice -eq "1") {
    # Check if entry already exists
    $content = Get-Content $HostsPath -Raw
    if ($content -match "upgrade.scdn.co") {
        Write-Host "Patch is already applied or upgrade.scdn.co is already defined in hosts file." -ForegroundColor Green
    } else {
        # Add entry
        Add-Content -Path $HostsPath -Value "`r`n$Comment`r`n$Entry"
        Write-Host "Patch enabled! upgrade.scdn.co now redirects to 127.0.0.1." -ForegroundColor Green
    }
}
elseif ($choice -eq "2") {
    # Remove entry
    if (Test-Path $HostsPath) {
        $lines = Get-Content $HostsPath
        $newLines = @()
        foreach ($line in $lines) {
            $trimmed = $line.Trim()
            if ($trimmed -eq $Comment) {
                continue
            }
            if ($trimmed -eq $Entry) {
                continue
            }
            # Also generic cleaning of upgrade.scdn.co
            if ($line -match "upgrade.scdn.co") {
                continue
            }
            $newLines += $line
        }
        $newLines | Out-File $HostsPath -Encoding ascii
        Write-Host "Patch disabled! upgrade.scdn.co redirection removed." -ForegroundColor Green
    }
}
else {
    Write-Host "Exiting."
}

Write-Host "Press any key to exit..."
[void][System.Console]::ReadKey($true)
