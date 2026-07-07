$path = [System.Environment]::GetEnvironmentVariable("PATH", "User")
$sp_dir = "$env:LOCALAPPDATA\spicetify"
$paths = ($path.Split(";") | Where-Object { $_.TrimEnd("\") -ne $sp_dir }) -join ";"
$is_in_path = "$path".Contains("$sp_dir") -or "$path".Contains("${sp_dir}")
if ($is_in_path) {[Environment]::SetEnvironmentVariable("PATH", "${paths}", "User")}
