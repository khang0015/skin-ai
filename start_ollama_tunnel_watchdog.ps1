# Keeps the SSH tunnel for Azure Ollama alive.
# If the Azure VM is off or SSH times out, this script waits and retries.

$KeyPath = "$PSScriptRoot\Khang_key.pem"
$VmUser = "azureuser"
$VmHost = "20.244.6.94"
$LocalPort = 11434
$RemotePort = 11434
$RetrySeconds = 30
$HealthUrl = "http://localhost:$LocalPort/api/tags"
$LogDir = "$PSScriptRoot\logs"
$LogPath = "$LogDir\ollama_tunnel_watchdog.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$MutexName = "Global\SkinAI_Ollama_Tunnel_Watchdog"
$Mutex = New-Object System.Threading.Mutex($false, $MutexName)
$HasMutex = $false

function Write-Log {
    param([string]$Message)
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$stamp] $Message" | Tee-Object -FilePath $LogPath -Append
}

function Test-OllamaLocal {
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -TimeoutSec 3 -UseBasicParsing
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

try {
    $HasMutex = $Mutex.WaitOne(0)
    if (-not $HasMutex) {
        Write-Log "Another Ollama tunnel watchdog is already running. Exiting."
        exit 0
    }
} catch {
    Write-Log "Could not acquire watchdog mutex: $_"
}

Write-Log "Ollama tunnel watchdog started."
Write-Log "Local URL: $HealthUrl"
Write-Log "Remote SSH: $VmUser@$VmHost, forward localhost:$LocalPort -> localhost:$RemotePort"

try {
    while ($true) {
        if (Test-OllamaLocal) {
            Write-Log "Ollama is reachable. Checking again in $RetrySeconds seconds."
            Start-Sleep -Seconds $RetrySeconds
            continue
        }

        Write-Log "Ollama is not reachable. Starting SSH tunnel..."

        & ssh `
            -i "$KeyPath" `
            -N `
            -L "${LocalPort}:localhost:${RemotePort}" `
            -o StrictHostKeyChecking=no `
            -o BatchMode=yes `
            -o ConnectTimeout=10 `
            -o ServerAliveInterval=30 `
            -o ServerAliveCountMax=3 `
            -o ExitOnForwardFailure=yes `
            "${VmUser}@${VmHost}"

        $exitCode = $LASTEXITCODE
        Write-Log "SSH tunnel stopped or failed. ExitCode=$exitCode. Retrying in $RetrySeconds seconds."
        Start-Sleep -Seconds $RetrySeconds
    }
} finally {
    if ($HasMutex) {
        $Mutex.ReleaseMutex() | Out-Null
    }
    $Mutex.Dispose()
}
