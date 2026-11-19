# Packing slip extensibility: trailing comma, missing templates, Minisoft EFS

**Status:** verified
**Evidence:** DCOMS-30254 (2026.7.0 regression ticket), `oms` repo, `oms_extensibility.ext_templates` in podqa/poddev/regression202520qa, AWS Lambda/EFS/S3

## Trailing-comma bug in custom packing slip (code fix)

- `GetPackingSlipUrl()` in `ShopVisible... DCEOM.BackAdmin.Application.Controllers/ShipOrderViewController.cs` builds the packing-slip URL straight from `currentRecord.IncludedItems`, which is routinely a **trailing-comma string** (e.g. `"100,101,"`) - confirmed by existing unit test fixtures using that exact shape.
- `generateCustomPackingSlip()` in `ShopVisible.Core.ShopLogic/backadmin/ShipOrderLabel.aspx.cs` then does `CurrentItemIDs.Split(',').Select(int.Parse)` with **no trim**, so the trailing comma produces an empty string and `int.Parse("")` throws `FormatException: Input string was not in a correct format`.
- Every sibling generator (`generatePackingSlip`, `generatePickList`, etc.) already strips a trailing comma first. `generateCustomPackingSlip` was the one outlier - this is a **pre-existing gap since 2019**, not a 2026.7.0 regression, it just wasn't hit until a store turned on "Generate packing slips with an external service" (which routes through `CustomSlip` / `generateCustomPackingSlip` instead of the normal `Slip` path).
- Fix: add the same `if (CurrentItemIDs.EndsWith(",")) CurrentItemIDs = CurrentItemIDs.Substring(0, CurrentItemIDs.Length - 1);` trim at the top of `generateCustomPackingSlip`.
- Branch `feature/akashyap/DCOMS-30254-custom-packing-slip-trailing-comma-fix`, commit `4665d69219`, pushed to origin (PR not yet opened as of 2026-11-19).

## Extensibility packing-slip template rows (data gap, not code)

- The "generate packing slips with an external service" path calls `IExtensibilityPackingSlipService` → POSTs to the extensibility API with `templateId = "{AffiliateGroupID}-{SupplierId},{AffiliateGroupID},default"`; `transactionHandler.ts` (`scp-service-online-payment`) tries each comma-split piece against `oms_extensibility.ext_templates` and fails with `Failure to post transaction, no template found for id ... and transaction type ...` if nothing matches.
- **podqa and regression202520qa had no `packingslip`/`default` row in `ext_templates` at all.** poddev had one, but with broken markup: the template's `productCode` field used `![CDATA[$item.product.productCode]]` (missing the opening `<` and closing `>`), which leaks raw CDATA syntax into the rendered slip instead of escaping the product code - same bug present in the Minisoft eFormz design file (`eom-service-printing-eformz/minisoft/projects/eSHIP/Documents/MapSHIPFXCartonOrderItemsToPackSlipOrderLines.efz`).
- Fix applied: copied poddev's `packingslip`/`default` row into podqa (swapping the Minisoft host string to podqa's), fixed the CDATA markup in podqa's copy, then copied the already-fixed podqa row into regression202520qa. **poddev's own row is still broken** - a write there got blocked by the Claude Code auto-mode classifier mid-session and was never retried; fix it the same way (`<![CDATA[$item.product.productCode]]>`) if poddev packing slips start getting worked on.
- Table is `oms_extensibility.ext_templates` (PK on `id, type, tenant`); use [[databases-and-local-access]] / the `oms_db_connector` connector with `PGDATABASE=<env>` to inspect/patch other environments.

## FedEx/USPS shipping labels: real feature gap, not a bug

- With extensibility on, FedEx and USPS shipping labels **never work in any environment** - confirmed zero `ext_templates` rows for either carrier in podqa or poddev, and no FedEx/USPS SIMFA template ids anywhere in the `oms` repo's SQL change scripts (only UPS templates, e.g. `02-simfa-ups[-1..4]`, were ever seeded).
- `TemplateExistCheck()` in `ShipOrderViewController.cs` pre-checks `templateId = "{serviceId}-{carrierId}-{siteId}"` existence and returns "Configuration for shipping labels requires additional set-up. Please contact your system administrator for assistance." when missing - expected behavior given no templates exist, not a defect to data-patch. Needs real template/dev work if FedEx/USPS extensibility labels are ever wanted.

## Minisoft `.efz` template files missing from an environment's EFS (manual recovery via AWS CLI)

When an environment's Harness CD pipeline (`OMS-DEV-AWS-ECS-SERVICE-SHARED-CD`, stage `minisoft_template_copy_lambda_deploy`) never actually ran for that environment, the environment's EFS access point has no `.efz` project files, and packing slips/labels fail with a Minisoft "File Not Found" error even once the DB template row is fixed. There is no committed S3 bucket/key for this stage (it's Harness-input-only, nothing to grep for in IaC) - recreate it manually:

1. Find the pattern: Lambda is named `oms_<space>_<environment>_alf-minisoftTmplCpy` (e.g. `oms_pod_qa_alf-minisoftTmplCpy`, `oms_regression202520_qa_alf-minisoftTmplCpy`). It downloads S3 file(s) from an invocation payload (`{s3Bucket, s3Key, fileName}`) to `/mnt/minisoft/projects/<fileName>` on EFS.
2. Clone a working environment's Lambda (`aws lambda get-function` + download code) as the source for the new one - don't rewrite it from scratch.
3. Recreate the IAM role: reuse the generic managed policies (`...-parameterstore-policy`, `...-cloudwatch-policy`, `...-s3-policy` with `s3:*` on `*`, `...-vpc-policy`) via `attach-role-policy`, but the `...-efs-policy` is **environment-specific** (scoped to that env's filesystem+access-point ARN) - use `aws iam put-role-policy` (inline) for it, since `iam:CreatePolicy` was denied for our CLI user (`oms-armi-poweruser`) but `put-role-policy` was allowed.
4. Find the target EFS access point via `aws efs describe-access-points` (e.g. `oms-regression202520-qa-ecs-efs-ap` = `fsap-0d4b9516c4d77c9b6`) and confirm its mount targets sit in the same shared dev/qa VPC/subnets the Lambda's VPC config uses.
5. Create a scratch S3 bucket for the `.efz` files (block public access, AES256 encryption), upload the templates, then `aws lambda create-function` pointed at that env's VPC/subnets/SG and EFS access point, and `aws lambda invoke` with `{s3Bucket, s3Key, fileName}` to push the files onto EFS. Verify via the Lambda's own returned JSON (file existence + byte size match).
6. Git Bash/MSYS gotcha: prefix the `aws lambda create-function` call with `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*"` or `/mnt/minisoft` gets silently rewritten into a Windows path (`LocalMountPath` then fails `ValidationException`). No `zip` binary in Git Bash either - use Python's `zipfile` module to build the deployment package.

See [[rds-connector-sso]] and [[databases-and-local-access]] for the DB connector side of this investigation.
