$ErrorActionPreference = 'SilentlyContinue'
$brokers = aws mq list-brokers --max-results 100 --output json | ConvertFrom-Json
$end = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$start = (Get-Date).AddDays(-14).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

$results = foreach ($b in $brokers.BrokerSummaries) {
    $id = $b.BrokerId
    $connJson = aws cloudwatch get-metric-statistics --namespace AWS/AmazonMQ --metric-name ConnectionCount --dimensions Name=Broker,Value=$id --start-time $start --end-time $end --period 86400 --statistics Maximum --output json
    $conn = $connJson | ConvertFrom-Json
    $maxConn = ($conn.Datapoints | Measure-Object -Property Maximum -Maximum).Maximum
    if ($null -eq $maxConn) { $maxConn = 0 }

    $pubJson = aws cloudwatch get-metric-statistics --namespace AWS/AmazonMQ --metric-name PublishRate --dimensions Name=Broker,Value=$id --start-time $start --end-time $end --period 86400 --statistics Maximum --output json
    $pub = $pubJson | ConvertFrom-Json
    $maxPub = ($pub.Datapoints | Measure-Object -Property Maximum -Maximum).Maximum
    if ($null -eq $maxPub) { $maxPub = 0 }

    $consJson = aws cloudwatch get-metric-statistics --namespace AWS/AmazonMQ --metric-name ConsumerCount --dimensions Name=Broker,Value=$id --start-time $start --end-time $end --period 86400 --statistics Maximum --output json
    $cons = $consJson | ConvertFrom-Json
    $maxCons = ($cons.Datapoints | Measure-Object -Property Maximum -Maximum).Maximum
    if ($null -eq $maxCons) { $maxCons = 0 }

    [PSCustomObject]@{
        Broker = $b.BrokerName
        BrokerId = $id
        Type = $b.HostInstanceType
        MaxConnections14d = [math]::Round([double]$maxConn, 1)
        MaxConsumers14d = [math]::Round([double]$maxCons, 1)
        MaxPublishRate14d = [math]::Round([double]$maxPub, 3)
        Used = if ($maxConn -gt 0 -or $maxPub -gt 0 -or $maxCons -gt 0) { 'YES' } else { 'NO' }
    }
}

$results | Sort-Object Used, MaxConnections14d -Descending | Format-Table -AutoSize
Write-Host ''
Write-Host "Total brokers: $($results.Count)"
Write-Host "Used (connections/publish/consumers > 0 in 14d): $(($results | Where-Object Used -eq 'YES').Count)"
Write-Host "Idle (zero activity in 14d): $(($results | Where-Object Used -eq 'NO').Count)"
