# Copyright 2019 khanhas. GPL license.
# Edited from project Denoland install script (https://github.com/denoland/deno_install)
# Edited to have no output, by OhItsTom.

param (
  [string] $version
)

$PSMinVersion = 3

if ($v) {
    $version = $v
}

if ($PSVersionTable.PSVersion.Major -gt $PSMinVersion) {
  $ErrorActionPreference = "Stop"

  # Enable TLS 1.2 since it is required for connections to GitHub.
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

  if (-not $version) {
    # Determine latest Spicetify release via GitHub API.
    $latest_release_uri =
    "https://api.github.com/repos/khanhas/spicetify-cli/releases/latest"
    $latest_release_json = Invoke-WebRequest -Uri $latest_release_uri -UseBasicParsing

    $version = ($latest_release_json | ConvertFrom-Json).tag_name -replace "v", ""
  }

  # Create ~\spicetify-cli directory if it doesn't already exist
  $sp_dir = "${HOME}\spicetify-cli"
  if (-not (Test-Path $sp_dir)) {
    New-Item -Path $sp_dir -ItemType Directory | Out-Null
  }

  # Download release.
  $zip_file = "${sp_dir}\spicetify-${version}-windows-x64.zip"
  $download_uri = "https://github.com/khanhas/spicetify-cli/releases/download/" +
  "v${version}/spicetify-${version}-windows-x64.zip"
  Invoke-WebRequest -Uri $download_uri -UseBasicParsing -OutFile $zip_file

  # Extract spicetify.exe and assets from .zip file.
  # Using -Force to overwrite spicetify.exe and assets if it already exists
  Expand-Archive -Path $zip_file -DestinationPath $sp_dir -Force

  # Remove .zip file.
  Remove-Item -Path $zip_file

  # Get Path environment variable for the current user.
  $user = [EnvironmentVariableTarget]::User
  $path = [Environment]::GetEnvironmentVariable("PATH", $user)

  # Check whether spicetify dir is in the Path.
  $paths = $path -split ";"
  $is_in_path = $paths -contains $sp_dir -or $paths -contains "${sp_dir}\"

  # Add Spicetify dir to PATH if it hasn't been added already.
  if (-not $is_in_path) {
    [Environment]::SetEnvironmentVariable("PATH", "${path};${sp_dir}", $user)
    # Add Spicetify to the PATH variable of the current terminal session
    # so `spicetify` can be used immediately without restarting the terminal.
    $env:PATH += ";${sp_dir}"
  }

}
else {
  Write-Host "`nYour Powershell version is lesser than "; Write-Emphasized "$PSMinVersion";
  Write-Host "`nPlease, update your Powershell downloading the "; Write-Emphasized "'Windows Management Framework'"; Write-Host " greater than "; Write-Emphasized "$PSMinVersion"
}
