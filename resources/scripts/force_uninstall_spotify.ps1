$spotifyExe = "$env:USERPROFILE\AppData\Roaming\Spotify\Spotify.exe"
if (Test-Path $spotifyExe) {
    & $spotifyExe /UNINSTALL /SILENT
}
icacls "$env:LOCALAPPDATA\Spotify\Update" /grant "${env:USERNAME}:D"
icacls "$env:LOCALAPPDATA\Spotify\Update" /grant "${env:USERNAME}:R"
