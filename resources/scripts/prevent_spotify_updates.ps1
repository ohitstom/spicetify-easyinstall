icacls "$env:LOCALAPPDATA\Spotify\Update" /deny "${env:USERNAME}:D"
icacls "$env:LOCALAPPDATA\Spotify\Update" /deny "${env:USERNAME}:R"
