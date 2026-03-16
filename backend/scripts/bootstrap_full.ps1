param(
  [string]$DatabaseUrl = "",
  [string]$Sources = "ibge,senado,camara,tse,portal_transparencia,pncp,base_dos_dados",
  [switch]$SkipMigrations,
  [switch]$SkipSeed,
  [switch]$ContinueOnError
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Split-Path -Parent $scriptDir
Set-Location $backendDir

if ($DatabaseUrl) {
  $env:DATABASE_URL = $DatabaseUrl
}

$python = ".\\.venv\\Scripts\\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}

$args = @("-m", "app.ops.bootstrap", "--sources", $Sources)
if ($SkipMigrations) { $args += "--skip-migrations" }
if ($SkipSeed) { $args += "--skip-seed" }
if ($ContinueOnError) { $args += "--continue-on-error" }

Write-Host "[bootstrap_full] Executando: $python $($args -join ' ')" -ForegroundColor Cyan
& $python @args

