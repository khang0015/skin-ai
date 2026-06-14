$TaskName = "SkinAI Ollama Tunnel Watchdog"
$ScriptPath = "$PSScriptRoot\start_ollama_tunnel_watchdog.ps1"

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""

$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Keeps the SSH tunnel to Azure Ollama alive for SkinAI." `
    -Force | Out-Null

Write-Host "Installed scheduled task: $TaskName"
Write-Host "It will start automatically when you log in to Windows."
Write-Host "Log file: $PSScriptRoot\logs\ollama_tunnel_watchdog.log"
