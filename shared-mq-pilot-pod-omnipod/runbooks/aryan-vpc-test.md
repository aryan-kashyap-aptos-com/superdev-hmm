# Manual + script setup in `aryan-vpc-test`

VPC: **vpc-0383e972f9d3826c4** (`aryan-vpc-test`)  
Account: **178918557969** | Region: **us-east-1**

Use a **new broker name** so it does not clash with the old one in the default VPC:

- `oms-aryan-vpc-test-mq-broker`

---

## Step 0 - Refresh AWS credentials

Your session token expired. Update:

`shared-mq-pilot-pod-omnipod/.aws-temp-credentials`

```ini
[temp-mq-admin]
aws_access_key_id=...
aws_secret_access_key=...
aws_session_token=...
```

---

## Step 1 - Preflight (script)

```powershell
cd C:\PROD\ConnectorSuite\shared-mq-pilot-pod-omnipod\scripts
.\Inspect-VpcForMq.ps1 -VpcId vpc-0383e972f9d3826c4
```

Fix anything marked **MISSING**:

| Check | Manual fix (AWS Console) |
|-------|--------------------------|
| No IGW | VPC → Internet gateways → Create → Attach to `aryan-vpc-test` |
| No `0.0.0.0/0` route | VPC → Route tables → add route `0.0.0.0/0` → IGW (must not be **blackhole**) |
| No subnets | VPC → Subnets → Create subnet in this VPC |
| No public subnet | Subnet settings → Enable auto-assign public IPv4 (optional, for bastion) |

---

## Step 2 - Create everything (script)

Copy **SubnetId** from inspect output, then:

```powershell
.\Provision-TempSharedMq.ps1 `
  -VpcId vpc-0383e972f9d3826c4 `
  -SubnetId <subnet-from-inspect> `
  -BrokerName oms-aryan-vpc-test-mq-broker `
  -OutputFile ..\baselines\temp-mq-provision-aryan-vpc.json
```

This creates: broker, vhosts, queues, SSM params. Output + passwords go to `baselines/temp-mq-provision-aryan-vpc.json`.

Optional bastion after:

```powershell
.\Setup-TempMqAccess.ps1
```

(Update that script to use the new VPC/subnet if bastion should live in `aryan-vpc-test`.)

---

## Step 2 alt - Fully manual in Console

### A. Amazon MQ

Amazon MQ → Create broker → RabbitMQ, single-instance, `mq.m7g.medium`, engine `3.13`, public **Yes**, VPC **aryan-vpc-test**, pick a subnet.

### B. RabbitMQ UI

Same as before: vhosts `pod-dev` / `omnipod-qa`, users, `main_exchange`, 6 queues, bindings.

### C. SSM Parameter Store

Update `/oms/shared/dev/aws-mq-broker/*`, `/oms/pod/dev/*`, `/oms/omnipod/qa/*` with **new** broker hostname.

---

## What differs from default VPC test

| | Default VPC (old) | aryan-vpc-test (new) |
|--|-------------------|----------------------|
| VPC | vpc-0c949a87c3e626568 | vpc-0383e972f9d3826c4 |
| Broker name | oms-shared-dev-mq-broker | oms-aryan-vpc-test-mq-broker |
| Output file | temp-mq-provision-output.json | temp-mq-provision-aryan-vpc.json |

Both brokers can exist at once; SSM will point to whichever you last wrote.

---

## After you refresh creds

Paste fresh creds into `.aws-temp-credentials` (or tell me the profile name), and say **run inspect** - I can check `aryan-vpc-test` and provision there for you.
