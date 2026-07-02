$ErrorActionPreference = "Stop"
$ports = 8000
Get-NetTCPConnection -LocalPort $ports -ErrorAction SilentlyContinue | ForEach-Object {
  Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
