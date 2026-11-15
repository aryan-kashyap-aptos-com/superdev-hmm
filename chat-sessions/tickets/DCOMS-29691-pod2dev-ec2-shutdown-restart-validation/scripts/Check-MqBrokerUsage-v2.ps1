$ErrorActionPreference = 'SilentlyContinue'
$brokers = aws mq list-brokers --max-results 100 --output json | ConvertFrom-Json
$end = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$start = (Get-Date).AddDays(-14).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

$results = foreach ($b in $brokers.BrokerSummaries) {
    $name = $b.BrokerName
    $connJson = aws cloudwatch get-metric-statistics --namespace AWS/AmazonMQ --metric-name ConnectionCount --dimensions Name=Broker,Value=$name --start-time $start --end-time $end --period 86400 --statistics Maximum --output json
    $conn = $connJson | ConvertFrom-Json
    $maxConn = ($conn.Datapoints | Measure-Object -Property Maximum -Maximum).Maximum
    if ($null -eq $maxConn) { $maxConn = 0 }

    $pubJson = aws cloudwatch get-metric-statistics --namespace AWS/AmazonMQ --metric-name PublishRate --dimensions Name=Broker,Value=$name --start-time $start --end-time $end --period 86400 --statistics Maximum --output json
    $pub = $pubJson | ConvertFrom-Json
    $maxPub = ($pub.Datapoints | Measure-Object -Property Maximum -Maximum).Maximum
    if ($null -eq $maxPub) { $maxPub = 0 }

    $consJson = aws cloudwatch get-metric-statistics --namespace AWS/AmazonMQ --metric-name ConsumerCount --dimensions Name=Broker,Value=$name --start-time $start --end-time $end --period 86400 --statistics Maximum --output json
    $cons = $consJson | ConvertFrom-Json
    $maxCons = ($cons.Datapoints | Measure-Object -Property Maximum -Maximum).Maximum
    if ($null -eq $maxCons) { $maxCons = 0 }

    [PSCustomObject]@{
        Broker = $name
        Type = $b.HostInstanceType
        MaxConnections14d = [math]::Round([double]$maxConn, 1)
        MaxConsumers14d = [math]::Round([double]$maxCons, 1)
        MaxPublishRate14d = [math]::Round([double]$maxPub, 3)
        Active14d = if ($maxConn -gt 0 -or $maxPub -gt 0 -or $maxCons -gt 0) { 'YES' } else { 'NO' }
    }
}

$results | Sort-Object Active14d, MaxConnections14d -Descending | Format-Table -AutoSize
Write-Host ''
Write-Host "Active in last 14d: $(($results | Where-Object Active14d -eq 'YES').Count)"
Write-Host "No CloudWatch activity in 14d: $(($results | Where-Object Active14d -eq 'NO').Count)"
