param(
  [string]$BaseUrl = "https://transparentegov.vercel.app",
  [string]$AdminKey = "change-this-admin-key"
)

$ErrorActionPreference = "Stop"

function Invoke-Check {
  param(
    [string]$Name,
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = @{}
  )

  $headersFile = New-TemporaryFile
  $bodyFile = New-TemporaryFile
  try {
    $args = @("-sS", "-L", "--max-time", "120", "-D", $headersFile.FullName, "-o", $bodyFile.FullName, "-X", $Method, $Url)
    foreach ($key in $Headers.Keys) {
      $args += @("-H", "${key}: $($Headers[$key])")
    }
    $null = & curl.exe @args

    $statusLine = (Get-Content $headersFile.FullName | Where-Object { $_ -match "^HTTP/" } | Select-Object -Last 1)
    if (-not $statusLine) {
      throw "Sem status HTTP na resposta."
    }

    $statusCode = [int]($statusLine.Split(" ")[1])
    $content = Get-Content $bodyFile.FullName -Raw
    if ($content.Length -gt 320) {
      $content = $content.Substring(0, 320) + "..."
    }

    if ($statusCode -ge 200 -and $statusCode -lt 300) {
      Write-Host "[OK] $Name -> $statusCode" -ForegroundColor Green
      Write-Host $content
    } else {
      Write-Host "[FAIL] $Name -> $statusCode" -ForegroundColor Red
      Write-Host $content
    }
  } catch {
    Write-Host "[FAIL] $Name -> $($_.Exception.Message)" -ForegroundColor Red
  } finally {
    Remove-Item $headersFile.FullName -ErrorAction SilentlyContinue
    Remove-Item $bodyFile.FullName -ErrorAction SilentlyContinue
  }
}

$adminHeaders = @{ "X-Admin-Key" = $AdminKey }

Invoke-Check -Name "health" -Method "GET" -Url "$BaseUrl/api/proxy/health"
Invoke-Check -Name "countries" -Method "GET" -Url "$BaseUrl/api/proxy/territory/countries"
Invoke-Check -Name "admin datasets" -Method "GET" -Url "$BaseUrl/api/proxy/admin/datasets" -Headers $adminHeaders
Invoke-Check -Name "collector runs" -Method "GET" -Url "$BaseUrl/api/proxy/collectors/runs" -Headers $adminHeaders
Invoke-Check -Name "run senado collector" -Method "POST" -Url "$BaseUrl/api/proxy/collectors/run/senado" -Headers $adminHeaders
