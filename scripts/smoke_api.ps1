$ErrorActionPreference = 'Stop'

function Login([string]$url){
  Write-Host 'Logging in...' -ForegroundColor Cyan
  $body = @{ username = 'admin'; password = 'admin123' } | ConvertTo-Json
  $resp = Invoke-RestMethod -Uri "$url/api/auth/login" -Method Post -ContentType 'application/json' -Body $body
  if (-not $resp.access_token) { throw 'No token' }
  return $resp.access_token
}

function Create-WorkCenter($baseUrl, $headers){
  $code = 'SMK-WC-' + ([guid]::NewGuid().ToString('N').Substring(0,5).ToUpper())
  $body = @{ code=$code; name='Smoke WC'; capacity=480; efficiency_pct=100 } | ConvertTo-Json
  $resp = Invoke-RestMethod -Uri "$baseUrl/api/production/work-centers" -Headers $headers -Method Post -ContentType 'application/json' -Body $body
  return $resp
}

function Create-MachineCenter($baseUrl, $headers, $wcCode){
  $code = 'SMK-MC-' + ([guid]::NewGuid().ToString('N').Substring(0,5).ToUpper())
  $body = @{ code=$code; name='Smoke MC'; work_center_code=$wcCode; capacity=480; efficiency_pct=100 } | ConvertTo-Json
  $resp = Invoke-RestMethod -Uri "$baseUrl/api/production/machine-centers" -Headers $headers -Method Post -ContentType 'application/json' -Body $body
  return $resp
}

function Try-Create-PO($baseUrl, $headers){
  try{
    $null = Invoke-RestMethod -Uri "$baseUrl/api/production/boms/certified/FG-DEMO-001" -Headers $headers -Method Get
  } catch {
    Write-Host 'No certified BOM for FG-DEMO-001 (skip PO)' -ForegroundColor Yellow
    return $null
  }
  $due = (Get-Date).AddDays(7).ToString('yyyy-MM-dd')
  $poNo = 'PO-SMOKE-' + ([guid]::NewGuid().ToString('N').Substring(0,4).ToUpper())
  $body = @{ order_no=$poNo; item_no='FG-DEMO-001'; quantity=5; due_date=$due; status='Planned'; priority=1 } | ConvertTo-Json
  $resp = Invoke-RestMethod -Uri "$baseUrl/api/production/production-orders" -Headers $headers -Method Post -ContentType 'application/json' -Body $body
  return $resp
}

$base = 'http://localhost:5000'
$token = Login $base
$headers = @{ Authorization = ('Bearer ' + $token) }

# Work centers list
$wcList = Invoke-RestMethod -Uri "$base/api/production/work-centers" -Headers $headers -Method Get
Write-Host ("WC total=" + $wcList.total)

# Create WC
$wc = Create-WorkCenter $base $headers
Write-Host ("WC created=" + $wc.code)

# Create MC
$mc = Create-MachineCenter $base $headers $wc.code
Write-Host ("MC created=" + $mc.code)

# Try create PO
$po = Try-Create-PO $base $headers
if ($po -ne $null){ Write-Host ("PO created=" + $po.order_no) }
