-- Read-only validation queries for ODX Feed Pipeline Monitor (DCOMS-29203)
-- Run manually on podqa / staging before or after deploying the monitor.

-- 1) Distinct task names and states in the last 24 hours
SELECT taskname,
       taskstate,
       result,
       COUNT(*) AS event_count
FROM oms.odxtasklogging
WHERE timestamputc >= NOW() - INTERVAL '24 hours'
GROUP BY taskname, taskstate, result
ORDER BY taskname, taskstate, result;

-- 2) Summary shape (matches OdxTaskLoggingRepository.GetSummaryByTaskNameAndState)
SELECT taskname,
       CASE
           WHEN taskstate = 'Done' AND result = 'Error' THEN 'Error'
           ELSE taskstate
       END AS taskstate,
       CAST(COUNT(*) AS INTEGER) AS task_state_count
FROM oms.odxtasklogging
WHERE timestamputc >= NOW() - INTERVAL '24 hours'
GROUP BY taskname,
         CASE
             WHEN taskstate = 'Done' AND result = 'Error' THEN 'Error'
             ELSE taskstate
         END
ORDER BY taskname, taskstate;

-- 3) Sample backlog messages (queued without done in same window)
SELECT DISTINCT q.messageid, q.taskname, q.referenceid, q.timestamputc
FROM oms.odxtasklogging q
WHERE q.taskstate = 'Queued'
  AND q.timestamputc >= NOW() - INTERVAL '24 hours'
  AND NOT EXISTS (
      SELECT 1
      FROM oms.odxtasklogging d
      WHERE d.messageid = q.messageid
        AND d.taskstate = 'Done'
        AND d.timestamputc >= NOW() - INTERVAL '24 hours'
  )
ORDER BY q.timestamputc DESC
LIMIT 20;

-- 4) Stuck omsfeedsqueuedorder rows (older than 24 hours)
SELECT orderid,
       queueddateutc,
       EXTRACT(EPOCH FROM (NOW() - queueddateutc)) / 3600 AS hours_in_queue
FROM oms.omsfeedsqueuedorder
WHERE queueddateutc < NOW() - INTERVAL '24 hours'
ORDER BY queueddateutc
LIMIT 20;

-- 5) Recent odxfeederror rows
SELECT errorid,
       feedtype,
       createdateutc,
       LEFT(error, 200) AS error_preview
FROM oms.odxfeederror
WHERE createdateutc >= NOW() - INTERVAL '24 hours'
ORDER BY createdateutc DESC
LIMIT 10;

-- 6) Search by reference id (replace 12345 with a real order/supplier id)
SELECT messageid,
       taskname,
       taskstate,
       result,
       referenceid,
       timestamputc
FROM oms.odxtasklogging
WHERE referenceid = 12345
  AND timestamputc >= NOW() - INTERVAL '24 hours'
ORDER BY timestamputc DESC
LIMIT 50;

-- 7) Timeline sample for one message id (replace with a real messageid)
SELECT id,
       messageid,
       taskname,
       taskstate,
       result,
       referenceid,
       timestamputc
FROM oms.odxtasklogging
WHERE messageid = 'REPLACE_WITH_MESSAGE_ID'
ORDER BY timestamputc;

-- 8) Check whether ODX Monitor resource exists
SELECT resource_id,
       resource_name,
       resource_alias,
       xml
FROM resources
WHERE LOWER(TRIM(xml)) = LOWER('OdxFeedMonitor.aspx');

-- 9) Service Manager resource used as role-copy source
SELECT resource_id,
       resource_name,
       resource_alias,
       xml
FROM resources
WHERE LOWER(TRIM(xml)) = LOWER('ServiceManager.aspx');

-- 10) Role mappings for ODX Monitor (after SQL script runs)
SELECT r.resource_name,
       r.xml,
       rvr.roleid
FROM resources r
JOIN rolesvsresources rvr ON rvr.resourceid = r.resource_id
WHERE LOWER(TRIM(r.xml)) = LOWER('OdxFeedMonitor.aspx')
ORDER BY rvr.roleid;
