# Temp account MQ access (178918557969)

## What is deployed

- Amazon MQ RabbitMQ broker: `oms-shared-dev-mq-broker`
- Vhosts: `pod-dev`, `omnipod-qa` (queues + `main_exchange`)
- SSM params under `/oms/shared/dev`, `/oms/pod/dev`, `/oms/omnipod/qa`
- SSM bastion: `i-0c9ab656c658d9f3a` (`oms-shared-mq-bastion`)
- VPC fixes: internet gateway, SSM VPC endpoints, default SG egress

Credentials and endpoints: `baselines/temp-mq-provision-output.json` (gitignored)

---

## Open RabbitMQ console (pick one)

### Option A - AWS Console (try first on corporate VPN)

1. Log into account **178918557969**, region **us-east-1**
2. Open: https://us-east-1.console.aws.amazon.com/amazon-mq/home?region=us-east-1#/brokers/details?id=b-52250a68-863c-4d48-9346-f2eca7363c0e
3. Click **RabbitMQ web console**
4. Login: `admin` + password from `temp-mq-provision-output.json`

### Option B - SSM port forward (if direct MQ URL is blocked)

Requires [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html).

```powershell
cd C:\PROD\ConnectorSuite\shared-mq-pilot-pod-omnipod\scripts
.\Open-TempMqConsole.ps1
```

Keep that window open. In browser open: **https://localhost:8443**

- Username: `admin`
- Password: from `temp-mq-provision-output.json`
- Accept certificate warning (cert is for the MQ hostname, not localhost)

### Option C - Direct URL (home network / off VPN)

https://b-52250a68-863c-4d48-9346-f2eca7363c0e.mq.us-east-1.on.aws

---

## Re-run setup / validation

```powershell
.\Setup-TempMqAccess.ps1
```

## Re-provision from scratch

```powershell
.\Provision-TempSharedMq.ps1
```
