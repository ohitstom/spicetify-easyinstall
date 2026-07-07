param(
    [string]$SpicetifyExe
)
& $SpicetifyExe config current_theme SpicetifyDefault -n
& $SpicetifyExe config check_spicetify_update 0 -n
& $SpicetifyExe backup apply enable-devtools -n 2>&1 | Where-Object { $_ -notmatch "offline\.bnk" }
