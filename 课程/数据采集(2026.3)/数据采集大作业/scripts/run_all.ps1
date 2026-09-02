param(
  [int]$Port = 8000,
  [int]$Target = 3500,
  [switch]$RefreshData,
  [switch]$NoOpen,
  [switch]$CheckOnly,
  [switch]$StrictRealData
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$dataFile = Join-Path $root "data\weather_clean.json"
$collectScript = Join-Path $root "scripts\collect_weather.py"
$processScript = Join-Path $root "scripts\process_weather.py"
$chartScript = Join-Path $root "scripts\generate_report_charts.py"
$excelScript = Join-Path $root "scripts\export_excel.py"
$demoScript = Join-Path $root "scripts\generate_weather_demo.ps1"
$serverScript = Join-Path $root "scripts\serve_static.ps1"

function Write-Step([string]$Message) {
  Write-Host ""
  Write-Host "==> $Message" -ForegroundColor Green
}

function Find-Python {
  $candidates = @()
  if ($env:PYTHON) { $candidates += $env:PYTHON }
  $candidates += "e:\python\python.exe"
  foreach ($name in @("python", "py")) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { $candidates += $cmd.Source }
  }

  foreach ($candidate in $candidates | Select-Object -Unique) {
    try {
      if ($candidate -and (Test-Path $candidate -PathType Leaf)) {
        & $candidate --version | Out-Null
        return $candidate
      }
    } catch {
      continue
    }
  }
  return $null
}

function Get-CleanRecordCount {
  if (-not (Test-Path $dataFile)) { return 0 }
  try {
    $rows = Get-Content -Raw -Encoding UTF8 $dataFile | ConvertFrom-Json
    return $rows.Count
  } catch {
    return 0
  }
}

function Use-DemoData {
  Write-Step "Generate demo weather data"
  & powershell -NoProfile -ExecutionPolicy Bypass -Command "`$code = Get-Content -Raw -Encoding UTF8 '$demoScript'; Invoke-Expression `$code"
}

function Use-LocalOrDemo {
  param([string]$Reason)
  $localCount = Get-CleanRecordCount
  if ($localCount -ge 3000) {
    Write-Host "$Reason Using existing local data with $localCount records." -ForegroundColor Yellow
    return
  }
  Write-Host "$Reason Local data is not enough, using demo data." -ForegroundColor Yellow
  Use-DemoData
}

function Test-PortBusy([int]$Value) {
  $client = New-Object System.Net.Sockets.TcpClient
  try {
    $async = $client.BeginConnect("127.0.0.1", $Value, $null, $null)
    $connected = $async.AsyncWaitHandle.WaitOne(250, $false)
    if ($connected -and $client.Connected) { return $true }
    return $false
  } catch {
    return $false
  } finally {
    $client.Close()
  }
}

Set-Location $root

$currentCount = Get-CleanRecordCount
if ($RefreshData -or $currentCount -lt 3000) {
  $python = Find-Python
  if ($python) {
    Write-Step "Try collecting real weather data"
    try {
      $collectArgs = @($collectScript)
      & $python @collectArgs
      if ($LASTEXITCODE -ne 0) { throw "weather collector exit code $LASTEXITCODE" }

      Write-Step "Clean and sync web data"
      & $python $processScript
      if ($LASTEXITCODE -ne 0) { throw "weather processor exit code $LASTEXITCODE" }
    } catch {
      if ($StrictRealData) {
        throw "Real weather collection failed and StrictRealData is enabled: $($_.Exception.Message)"
      }
      Use-LocalOrDemo "Real weather collection failed: $($_.Exception.Message)."
    }
  } else {
    if ($StrictRealData) {
      throw "Python was not found and StrictRealData is enabled."
    }
    Use-LocalOrDemo "Python was not found."
  }
} else {
  Write-Step "Found $currentCount existing weather records, starting web app"
}

$finalCount = Get-CleanRecordCount
if ($finalCount -lt 3000) {
  Write-Host "Data is below 3000 records, regenerating demo data." -ForegroundColor Yellow
  Use-DemoData
  $finalCount = Get-CleanRecordCount
}

if ($CheckOnly) {
  Write-Step "Check complete"
  Write-Host "Records: $finalCount"
  return
}

$chartPython = Find-Python
if ($chartPython -and (Test-Path $chartScript)) {
  Write-Step "Generate report chart images"
  try {
    & $chartPython $chartScript
    if ($LASTEXITCODE -ne 0) { throw "chart generator exit code $LASTEXITCODE" }
  } catch {
    Write-Host "Report chart generation failed: $($_.Exception.Message)" -ForegroundColor Yellow
  }
} else {
  Write-Host "Skip report chart generation because Python or chart script was not found." -ForegroundColor Yellow
}

$excelPython = Find-Python
if ($excelPython -and (Test-Path $excelScript)) {
  Write-Step "Export weather data to Excel"
  try {
    & $excelPython $excelScript
    if ($LASTEXITCODE -ne 0) { throw "Excel export exit code $LASTEXITCODE" }
  } catch {
    Write-Host "Excel export failed: $($_.Exception.Message)" -ForegroundColor Yellow
  }
} else {
  Write-Host "Skip Excel export because Python or export script was not found." -ForegroundColor Yellow
}

while (Test-PortBusy $Port) {
  $Port += 1
}

$url = "http://localhost:$Port/frontend/index.html"
Write-Step "Start web server"
Write-Host "Records: $finalCount"
Write-Host "URL: $url"
Write-Host "Close this window to stop the server."

if (-not $NoOpen) {
  Start-Process $url
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $serverScript -Port $Port
