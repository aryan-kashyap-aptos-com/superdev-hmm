Get-Website | Select-Object Name, State, PhysicalPath | Format-Table -AutoSize
Get-ChildItem -Path 'C:\' -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'OMS|Shop|Aptos|inetpub' } | Select Name, FullName
if (Test-Path 'D:\') { Get-ChildItem -Path 'D:\' -Directory -ErrorAction SilentlyContinue | Select Name, FullName }
