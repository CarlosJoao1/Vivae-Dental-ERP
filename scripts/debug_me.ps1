$ErrorActionPreference='Stop'
$base='http://localhost:5000'
$body=@{username='admin';password='admin123'} | ConvertTo-Json
$r=Invoke-RestMethod -Uri "$base/api/auth/login" -Method Post -ContentType 'application/json' -Body $body
$token=$r.access_token
if(-not $token){ throw 'No token' }
$headers=@{Authorization=('Bearer ' + $token)}
$me=Invoke-RestMethod -Uri "$base/api/auth/me" -Headers $headers -Method Get
$me | ConvertTo-Json -Compress | Write-Output
