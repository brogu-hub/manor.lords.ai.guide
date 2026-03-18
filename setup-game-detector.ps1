# Manor Lords AI Advisor — Game Detector Setup
# Adds auto-open browser when Manor Lords launches via Steam.
# Run once: .\setup-game-detector.ps1

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $projectDir "game_detector_service.pyw"

if (-not (Test-Path $scriptPath)) {
    Write-Host "Error: game_detector_service.pyw not found in $projectDir" -ForegroundColor Red
    exit 1
}

# Check Python is available
$pythonw = Get-Command pythonw -ErrorAction SilentlyContinue
if (-not $pythonw) {
    Write-Host "Error: pythonw not found. Install Python and ensure it's in PATH." -ForegroundColor Red
    exit 1
}

# Create startup shortcut
$startupDir = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupDir "ManorLordsDetector.lnk"

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = $pythonw.Source
$sc.Arguments = "`"$scriptPath`""
$sc.WorkingDirectory = $projectDir
$sc.Description = "Auto-open Manor Lords Advisor when game launches"
$sc.WindowStyle = 7  # Minimized
$sc.Save()

Write-Host ""
Write-Host "Game detector installed!" -ForegroundColor Green
Write-Host "  Shortcut: $shortcutPath" -ForegroundColor DarkGray
Write-Host ""
Write-Host "It will start automatically on login." -ForegroundColor Cyan
Write-Host "Starting it now..." -ForegroundColor Cyan

# Start immediately
Start-Process pythonw -ArgumentList "`"$scriptPath`"" -WorkingDirectory $projectDir

Write-Host "Done. Dashboard will open when Manor Lords launches." -ForegroundColor Green
