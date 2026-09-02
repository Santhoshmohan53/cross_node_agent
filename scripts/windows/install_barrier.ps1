# Install Barrier silently on Windows
$installer = Join-Path $env:TEMP "BarrierSetup-2.4.0.exe"
if (-not (Test-Path $installer)) {
    Write-Host "Downloading Barrier..."
    $url = "https://github.com/debauchee/barrier/releases/download/v2.4.0/BarrierSetup-2.4.0-release.exe"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
}

Write-Host "Running Barrier installer..."
$proc = Start-Process -FilePath $installer -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-" -PassThru -Wait
Write-Host "Installer Finished with Exit Code: $($proc.ExitCode)"

$progFiles = "${env:ProgramFiles}\Barrier\barriers.exe"
if (Test-Path $progFiles) {
    Write-Host "[SUCCESS] Barrier installed at $progFiles"
} else {
    Write-Host "[INFO] Checking other paths..."
    Get-ChildItem "${env:ProgramFiles}\Barrier", "${env:ProgramFiles(x86)}\Barrier" -ErrorAction SilentlyContinue
}
