# Terraform files by stack root

**Terraform roots:** 62
**Total `.tf` files:** 974

## `01-infrastructure/00-aws-kms` (4 files)

- `01-infrastructure/00-aws-kms/1-versions.tf`
- `01-infrastructure/00-aws-kms/2-generic-variables.tf`
- `01-infrastructure/00-aws-kms/3-local-values.tf`
- `01-infrastructure/00-aws-kms/4-01-kms-resource.tf`

## `01-infrastructure/01-parameterstore` (6 files)

- `01-infrastructure/01-parameterstore/0-terraform-remote-state-datasource.tf`
- `01-infrastructure/01-parameterstore/1-versions.tf`
- `01-infrastructure/01-parameterstore/2-generic-variables.tf`
- `01-infrastructure/01-parameterstore/3-local-values.tf`
- `01-infrastructure/01-parameterstore/4-02-parameterstore-variables.tf`
- `01-infrastructure/01-parameterstore/4-03-parameterstore-resource.tf`

## `01-infrastructure/02-vpc-infrastructure` (23 files)

- `01-infrastructure/02-vpc-infrastructure/1-versions.tf`
- `01-infrastructure/02-vpc-infrastructure/2-generic-variables.tf`
- `01-infrastructure/02-vpc-infrastructure/3-local-values.tf`
- `01-infrastructure/02-vpc-infrastructure/4-01-vpc-variables.tf`
- `01-infrastructure/02-vpc-infrastructure/4-02-vpc-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/4-03-vpc-outputs.tf`
- `01-infrastructure/02-vpc-infrastructure/5-01-securitygroup-variables.tf`
- `01-infrastructure/02-vpc-infrastructure/5-02-securitygroup-outputs.tf`
- `01-infrastructure/02-vpc-infrastructure/5-03-securitygroup-bastionsg-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/5-04-securitygroup-mqbrokersg-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/5-04-securitygroup-privatesg-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/5-05-securitygroup-rdsdbsg-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/5-06-securitygroup-nfssg-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/5-07-securitygroup-lambdasg-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/5-08-securitygroup-ecssg-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/5-09-securitygroup-loadbalancersg-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/6-01-datasource-variables.tf`
- `01-infrastructure/02-vpc-infrastructure/6-02-datasource-ami.tf`
- `01-infrastructure/02-vpc-infrastructure/7-01-ec2instance-variables.tf`
- `01-infrastructure/02-vpc-infrastructure/7-02-ec2instance-outputs.tf`
- `01-infrastructure/02-vpc-infrastructure/7-03-ec2instance-bastion-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/8-elasticip-resource.tf`
- `01-infrastructure/02-vpc-infrastructure/9-nullresource-provisioners.tf`

## `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master` (17 files)

- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/0-terraform-remote-state-datasource.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/1-versions.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/10-01-rds-db-metrics.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/10-02-rds-db-metrics-variables.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/11-01-rds-lambda-connect.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/2-generic-variables.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/3-local-values.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/4-01-datasource-parameterstore.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/5-01-rds-secretmanager-resource.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/5-02-rds-secretmanager-output.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/6-01-rdsdb-variables.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/6-02-rdsdb-resource.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/6-03-rdsdb-dataapi-access-policy.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/8-01-rds-proxy-resource.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/8-02-rds-md5-proxy-resource.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/8-03-rds-proxy-output.tf`
- `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master/9-01-parameterstore-resource.tf`

## `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision` (12 files)

- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/0-terraform-remote-state-datasource.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/1-versions.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/2-generic-variables.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/3-local-values.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/4-01-datasource-parameterstore.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/5-01-rds-secretmanager-resource.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/5-02-rds-secretmanager-output.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/6-01-rdsdb-variables.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/6-02-rdsdb-dataapi-access-policy.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/7-01-rds-proxy-resource.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/7-02-rds-md5-proxy-resource.tf`
- `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision/8-01-parameterstore-resource.tf`

## `01-infrastructure/04-awsmq-broker-infrastructure` (9 files)

- `01-infrastructure/04-awsmq-broker-infrastructure/0-terraform-remote-state-datasource.tf`
- `01-infrastructure/04-awsmq-broker-infrastructure/1-versions.tf`
- `01-infrastructure/04-awsmq-broker-infrastructure/2-generic-variables.tf`
- `01-infrastructure/04-awsmq-broker-infrastructure/3-local-values.tf`
- `01-infrastructure/04-awsmq-broker-infrastructure/4-01-datasource-parameterstore.tf`
- `01-infrastructure/04-awsmq-broker-infrastructure/5-01-mqbroker-variables.tf`
- `01-infrastructure/04-awsmq-broker-infrastructure/5-02-mqbroker-resource.tf`
- `01-infrastructure/04-awsmq-broker-infrastructure/5-03-mqbroker-output.tf`
- `01-infrastructure/04-awsmq-broker-infrastructure/6-01-parameterstore-resource.tf`

## `01-infrastructure/05-vpc-peering/01-15-existing-core` (5 files)

- `01-infrastructure/05-vpc-peering/01-15-existing-core/1-versions.tf`
- `01-infrastructure/05-vpc-peering/01-15-existing-core/2-generic-variables.tf`
- `01-infrastructure/05-vpc-peering/01-15-existing-core/3-local-values.tf`
- `01-infrastructure/05-vpc-peering/01-15-existing-core/4-01-main_variable.tf`
- `01-infrastructure/05-vpc-peering/01-15-existing-core/4-02-main.tf`

## `01-infrastructure/05-vpc-peering/02-15-15` (5 files)

- `01-infrastructure/05-vpc-peering/02-15-15/1-versions.tf`
- `01-infrastructure/05-vpc-peering/02-15-15/2-generic-variables.tf`
- `01-infrastructure/05-vpc-peering/02-15-15/3-local-values.tf`
- `01-infrastructure/05-vpc-peering/02-15-15/4-01-main_variable.tf`
- `01-infrastructure/05-vpc-peering/02-15-15/4-02-main.tf`

## `01-infrastructure/05-vpc-peering/02-15-new-core` (5 files)

- `01-infrastructure/05-vpc-peering/02-15-new-core/1-versions.tf`
- `01-infrastructure/05-vpc-peering/02-15-new-core/2-generic-variables.tf`
- `01-infrastructure/05-vpc-peering/02-15-new-core/3-local-values.tf`
- `01-infrastructure/05-vpc-peering/02-15-new-core/4-01-main_variable.tf`
- `01-infrastructure/05-vpc-peering/02-15-new-core/4-02-main.tf`

## `01-infrastructure/05-vpc-peering/03-harness-new-core` (5 files)

- `01-infrastructure/05-vpc-peering/03-harness-new-core/1-versions.tf`
- `01-infrastructure/05-vpc-peering/03-harness-new-core/2-generic-variables.tf`
- `01-infrastructure/05-vpc-peering/03-harness-new-core/3-local-values.tf`
- `01-infrastructure/05-vpc-peering/03-harness-new-core/4-01-main_variable.tf`
- `01-infrastructure/05-vpc-peering/03-harness-new-core/4-02-main.tf`

## `01-infrastructure/05-vpc-peering/04-15-harness` (5 files)

- `01-infrastructure/05-vpc-peering/04-15-harness/1-versions.tf`
- `01-infrastructure/05-vpc-peering/04-15-harness/2-generic-variables.tf`
- `01-infrastructure/05-vpc-peering/04-15-harness/3-local-values.tf`
- `01-infrastructure/05-vpc-peering/04-15-harness/4-01-main_variable.tf`
- `01-infrastructure/05-vpc-peering/04-15-harness/4-02-main.tf`

## `01-infrastructure/05-vpc-peering/05-new-core-existing-core` (5 files)

- `01-infrastructure/05-vpc-peering/05-new-core-existing-core/1-versions.tf`
- `01-infrastructure/05-vpc-peering/05-new-core-existing-core/2-generic-variables.tf`
- `01-infrastructure/05-vpc-peering/05-new-core-existing-core/3-local-values.tf`
- `01-infrastructure/05-vpc-peering/05-new-core-existing-core/4-01-main_variable.tf`
- `01-infrastructure/05-vpc-peering/05-new-core-existing-core/4-02-main.tf`

## `01-infrastructure/07-beanstalk` (4 files)

- `01-infrastructure/07-beanstalk/1-versions.tf`
- `01-infrastructure/07-beanstalk/2-generic-variables.tf`
- `01-infrastructure/07-beanstalk/3-local-values.tf`
- `01-infrastructure/07-beanstalk/4-02-main-with-lb.tf`

## `01-infrastructure/08-core/projects/eom-terraform-master/parameterstore` (4 files)

- `01-infrastructure/08-core/projects/eom-terraform-master/parameterstore/1-versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/parameterstore/2-generic-variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/parameterstore/3-01-parameterstore-variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/parameterstore/3-02-parameterstore-resource.tf`

## `01-infrastructure/09-usergroup` (5 files)

- `01-infrastructure/09-usergroup/1-versions.tf`
- `01-infrastructure/09-usergroup/2-generic-variables.tf`
- `01-infrastructure/09-usergroup/3-local-values.tf`
- `01-infrastructure/09-usergroup/4-01-readonly-policy.tf`
- `01-infrastructure/09-usergroup/4-02-manage-policy.tf`

## `01-infrastructure/10-transitgateway` (6 files)

- `01-infrastructure/10-transitgateway/0-terraform-remote-state-datasource.tf`
- `01-infrastructure/10-transitgateway/1-versions.tf`
- `01-infrastructure/10-transitgateway/2-generic-variables.tf`
- `01-infrastructure/10-transitgateway/3-local-values.tf`
- `01-infrastructure/10-transitgateway/4-01-transitgateway-variables.tf`
- `01-infrastructure/10-transitgateway/4-02-transitgateway-association.tf`

## `01-infrastructure/11-vpc-endpoints` (6 files)

- `01-infrastructure/11-vpc-endpoints/0-terraform-remote-state-datasource.tf`
- `01-infrastructure/11-vpc-endpoints/1-versions.tf`
- `01-infrastructure/11-vpc-endpoints/2-generic-variables.tf`
- `01-infrastructure/11-vpc-endpoints/3-local-values.tf`
- `01-infrastructure/11-vpc-endpoints/4-01-vpc-endpoints-lambda.tf`
- `01-infrastructure/11-vpc-endpoints/5-01-aurora-lambda-egress.tf`

## `02-platform/01-ecs-cluster` (13 files)

- `02-platform/01-ecs-cluster/0-terraform-remote-state-datasource.tf`
- `02-platform/01-ecs-cluster/1-versions.tf`
- `02-platform/01-ecs-cluster/2-generic-variables.tf`
- `02-platform/01-ecs-cluster/3-local-values.tf`
- `02-platform/01-ecs-cluster/4-01-efs-resource.tf`
- `02-platform/01-ecs-cluster/4-02-efs-output.tf`
- `02-platform/01-ecs-cluster/5-01-datasource-iam-policy.tf`
- `02-platform/01-ecs-cluster/6-01-apigateway-resources.tf`
- `02-platform/01-ecs-cluster/6-02-apigateway-output.tf`
- `02-platform/01-ecs-cluster/7-01-ecs-cluster-iam-roles-policy-resources.tf`
- `02-platform/01-ecs-cluster/7-02-ecs-cluster-resources.tf`
- `02-platform/01-ecs-cluster/7-03-ecs-cluster-output.tf`
- `02-platform/01-ecs-cluster/8-01-servicediscovery.tf`

## `02-platform/02-s3-staticweb` (10 files)

- `02-platform/02-s3-staticweb/0-terraform-remote-state-datasource.tf`
- `02-platform/02-s3-staticweb/1-versions.tf`
- `02-platform/02-s3-staticweb/2-generic-variables.tf`
- `02-platform/02-s3-staticweb/3-local-values.tf`
- `02-platform/02-s3-staticweb/4-01-s3-staticweb-variables.tf`
- `02-platform/02-s3-staticweb/4-02-s3-staticweb-resources.tf`
- `02-platform/02-s3-staticweb/4-03-s3-acm-resources.tf`
- `02-platform/02-s3-staticweb/4-04-s3-staticweb-cloudfront-resources.tf`
- `02-platform/02-s3-staticweb/4-05-s3-staticweb-route53-dnsregistration.tf`
- `02-platform/02-s3-staticweb/4-06-s3-staticweb-output.tf`

## `02-platform/03-aws-batch/01-aws-batch-sql-job` (10 files)

- `02-platform/03-aws-batch/01-aws-batch-sql-job/0-terraform-remote-state-datasource.tf`
- `02-platform/03-aws-batch/01-aws-batch-sql-job/1-versions.tf`
- `02-platform/03-aws-batch/01-aws-batch-sql-job/2-generic-variables.tf`
- `02-platform/03-aws-batch/01-aws-batch-sql-job/3-local-values.tf`
- `02-platform/03-aws-batch/01-aws-batch-sql-job/4-01-datasource-iam-policy.tf`
- `02-platform/03-aws-batch/01-aws-batch-sql-job/4-02-batch-variable.tf`
- `02-platform/03-aws-batch/01-aws-batch-sql-job/4-03-aws-batch-iam-roles-policy-resources.tf`
- `02-platform/03-aws-batch/01-aws-batch-sql-job/4-04-aws-batch-compute_env.tf`
- `02-platform/03-aws-batch/01-aws-batch-sql-job/4-05-aws-batch-job-queue.tf`
- `02-platform/03-aws-batch/01-aws-batch-sql-job/4-06-aws-batch-output.tf`

## `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform` (9 files)

- `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform/0-terraform-remote-state-datasource.tf`
- `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform/1-versions.tf`
- `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform/11-batch-platform-metadata-ssm.tf`
- `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform/2-variables.tf`
- `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform/3-local-values.tf`
- `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform/6-iam-batch-service-role.tf`
- `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform/7-batch-compute-environment.tf`
- `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform/8-batch-job-queue.tf`
- `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform/9-outputs.tf`

## `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db` (9 files)

- `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db/1-versions.tf`
- `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db/2-variables.tf`
- `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db/3-local-values.tf`
- `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db/4-datasource-parameterstore.tf`
- `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db/5-datasource-remote-state.tf`
- `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db/6-render-catalog-sql.tf`
- `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db/7-check-ssh-key.tf`
- `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db/9-outputs.tf`
- `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db/Main.tf`

## `02-platform/04-aws-lambda-layer` (3 files)

- `02-platform/04-aws-lambda-layer/1-versions.tf`
- `02-platform/04-aws-lambda-layer/2-generic-variables.tf`
- `02-platform/04-aws-lambda-layer/3-01-layer-resource.tf`

## `03-application/01-aws-ecs-service/01-currencyexchange` (10 files)

- `03-application/01-aws-ecs-service/01-currencyexchange/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/01-currencyexchange/1-versions.tf`
- `03-application/01-aws-ecs-service/01-currencyexchange/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/01-currencyexchange/3-local-values.tf`
- `03-application/01-aws-ecs-service/01-currencyexchange/4-01-currencyexchange-variables.tf`
- `03-application/01-aws-ecs-service/01-currencyexchange/4-02-currencyexchange-alb-resources.tf`
- `03-application/01-aws-ecs-service/01-currencyexchange/4-03-currencyexchange-route53-dnsregistration.tf`
- `03-application/01-aws-ecs-service/01-currencyexchange/4-04-currencyexchange-taskdefinition.tf`
- `03-application/01-aws-ecs-service/01-currencyexchange/4-05-currencyexchange-service-resource.tf`
- `03-application/01-aws-ecs-service/01-currencyexchange/4-06-currencyexchange-output.tf`

## `03-application/01-aws-ecs-service/02-efs-fileexplorer` (9 files)

- `03-application/01-aws-ecs-service/02-efs-fileexplorer/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/02-efs-fileexplorer/1-versions.tf`
- `03-application/01-aws-ecs-service/02-efs-fileexplorer/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/02-efs-fileexplorer/3-local-values.tf`
- `03-application/01-aws-ecs-service/02-efs-fileexplorer/4-01-efs-fileexplorer-variables.tf`
- `03-application/01-aws-ecs-service/02-efs-fileexplorer/4-02-efs-fileexplorer-alb-resources.tf`
- `03-application/01-aws-ecs-service/02-efs-fileexplorer/4-04-efs-fileexplorer-taskdefinition.tf`
- `03-application/01-aws-ecs-service/02-efs-fileexplorer/4-05-efs-fileexplorer-service-resource.tf`
- `03-application/01-aws-ecs-service/02-efs-fileexplorer/4-06-efs-fileexplorer-output.tf`

## `03-application/01-aws-ecs-service/03-keycloak` (12 files)

- `03-application/01-aws-ecs-service/03-keycloak/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/03-keycloak/1-versions.tf`
- `03-application/01-aws-ecs-service/03-keycloak/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/03-keycloak/3-local-values.tf`
- `03-application/01-aws-ecs-service/03-keycloak/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/03-keycloak/5-01-keycloak-variables.tf`
- `03-application/01-aws-ecs-service/03-keycloak/5-02-keycloak-alb-resources.tf`
- `03-application/01-aws-ecs-service/03-keycloak/5-04-keycloak-taskdefinition.tf`
- `03-application/01-aws-ecs-service/03-keycloak/5-05-keycloak-service-resource.tf`
- `03-application/01-aws-ecs-service/03-keycloak/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/03-keycloak/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/03-keycloak/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/04-minisoft` (12 files)

- `03-application/01-aws-ecs-service/04-minisoft/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/04-minisoft/1-versions.tf`
- `03-application/01-aws-ecs-service/04-minisoft/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/04-minisoft/3-local-values.tf`
- `03-application/01-aws-ecs-service/04-minisoft/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/04-minisoft/4-02-minisoft-alb-resources.tf`
- `03-application/01-aws-ecs-service/04-minisoft/5-01-minisoft-variables.tf`
- `03-application/01-aws-ecs-service/04-minisoft/5-04-minisoft-taskdefinition.tf`
- `03-application/01-aws-ecs-service/04-minisoft/5-05-minisoft-service-resource.tf`
- `03-application/01-aws-ecs-service/04-minisoft/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/04-minisoft/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/04-minisoft/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/05-extensibility` (12 files)

- `03-application/01-aws-ecs-service/05-extensibility/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/05-extensibility/1-versions.tf`
- `03-application/01-aws-ecs-service/05-extensibility/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/05-extensibility/3-local-values.tf`
- `03-application/01-aws-ecs-service/05-extensibility/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/05-extensibility/5-01-extensibility-variables.tf`
- `03-application/01-aws-ecs-service/05-extensibility/5-04-extensibility-taskdefinition.tf`
- `03-application/01-aws-ecs-service/05-extensibility/5-05-extensibility-service-resource.tf`
- `03-application/01-aws-ecs-service/05-extensibility/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/05-extensibility/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/05-extensibility/7-01-parameterstore-resource.tf`
- `03-application/01-aws-ecs-service/05-extensibility/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/06-taskscheduler` (12 files)

- `03-application/01-aws-ecs-service/06-taskscheduler/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/1-versions.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/3-local-values.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/5-01-taskscheduler-variables.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/5-02-taskscheduler-alb-resources.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/5-04-taskscheduler-taskdefinition.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/5-05-taskscheduler-service-resource.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/06-taskscheduler/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/07-omsfeed` (8 files)

- `03-application/01-aws-ecs-service/07-omsfeed/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/07-omsfeed/1-versions.tf`
- `03-application/01-aws-ecs-service/07-omsfeed/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/07-omsfeed/3-local-values.tf`
- `03-application/01-aws-ecs-service/07-omsfeed/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/07-omsfeed/5-01-omsfeed-variables.tf`
- `03-application/01-aws-ecs-service/07-omsfeed/5-02-omsfeed-taskdefinition.tf`
- `03-application/01-aws-ecs-service/07-omsfeed/5-03-omsfeed-service-resource.tf`

## `03-application/01-aws-ecs-service/08-omsinventoryfeed` (8 files)

- `03-application/01-aws-ecs-service/08-omsinventoryfeed/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/08-omsinventoryfeed/1-versions.tf`
- `03-application/01-aws-ecs-service/08-omsinventoryfeed/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/08-omsinventoryfeed/3-local-values.tf`
- `03-application/01-aws-ecs-service/08-omsinventoryfeed/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/08-omsinventoryfeed/5-01-omsinventoryfeed-variables.tf`
- `03-application/01-aws-ecs-service/08-omsinventoryfeed/5-02-omsinventoryfeed-taskdefinition.tf`
- `03-application/01-aws-ecs-service/08-omsinventoryfeed/5-03-omsinventoryfeed-service-resource.tf`

## `03-application/01-aws-ecs-service/09-taskprocessor` (8 files)

- `03-application/01-aws-ecs-service/09-taskprocessor/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/09-taskprocessor/1-versions.tf`
- `03-application/01-aws-ecs-service/09-taskprocessor/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/09-taskprocessor/3-local-values.tf`
- `03-application/01-aws-ecs-service/09-taskprocessor/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/09-taskprocessor/5-01-taskprocessor-variables.tf`
- `03-application/01-aws-ecs-service/09-taskprocessor/5-02-taskprocessor-taskdefinition.tf`
- `03-application/01-aws-ecs-service/09-taskprocessor/5-03-taskprocessor-service-resource.tf`

## `03-application/01-aws-ecs-service/10-orderfacade` (12 files)

- `03-application/01-aws-ecs-service/10-orderfacade/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/1-versions.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/3-local-values.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/5-01-orderfacade-variables.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/5-02-orderfacade-alb-resources.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/5-04-orderfacade-taskdefinition.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/5-05-orderfacade-service-resource.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/10-orderfacade/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/11-inventoryfacade` (12 files)

- `03-application/01-aws-ecs-service/11-inventoryfacade/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/1-versions.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/3-local-values.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/5-01-inventoryfacade-variables.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/5-02-inventoryfacade-alb-resources.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/5-04-inventoryfacade-taskdefinition.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/5-05-inventoryfacade-service-resource.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/11-inventoryfacade/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/15-configrulemanager` (12 files)

- `03-application/01-aws-ecs-service/15-configrulemanager/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/1-versions.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/3-local-values.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/5-01-configrulemanager-variables.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/5-02-configrulemanager-alb-resources.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/5-04-configrulemanager-taskdefinition.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/5-05-configrulemanager-service-resource.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/15-configrulemanager/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/16-coreapi` (12 files)

- `03-application/01-aws-ecs-service/16-coreapi/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/16-coreapi/1-versions.tf`
- `03-application/01-aws-ecs-service/16-coreapi/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/16-coreapi/3-local-values.tf`
- `03-application/01-aws-ecs-service/16-coreapi/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/16-coreapi/5-01-coreapi-variables.tf`
- `03-application/01-aws-ecs-service/16-coreapi/5-04-coreapi-taskdefinition.tf`
- `03-application/01-aws-ecs-service/16-coreapi/5-05-coreapi-service-resource.tf`
- `03-application/01-aws-ecs-service/16-coreapi/5-06-coreapi-autoscaling.tf`
- `03-application/01-aws-ecs-service/16-coreapi/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/16-coreapi/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/16-coreapi/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/17-coreservice` (12 files)

- `03-application/01-aws-ecs-service/17-coreservice/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/17-coreservice/1-versions.tf`
- `03-application/01-aws-ecs-service/17-coreservice/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/17-coreservice/3-local-values.tf`
- `03-application/01-aws-ecs-service/17-coreservice/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/17-coreservice/5-01-coreservice-variables.tf`
- `03-application/01-aws-ecs-service/17-coreservice/5-04-coreservice-taskdefinition.tf`
- `03-application/01-aws-ecs-service/17-coreservice/5-05-coreservice-service-resource.tf`
- `03-application/01-aws-ecs-service/17-coreservice/5-06-coreapi-autoscaling.tf`
- `03-application/01-aws-ecs-service/17-coreservice/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/17-coreservice/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/17-coreservice/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/18-corepaymentapi` (12 files)

- `03-application/01-aws-ecs-service/18-corepaymentapi/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/1-versions.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/3-local-values.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/5-01-corepaymentapi-variables.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/5-04-corepaymentapi-taskdefinition.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/5-05-corepaymentapi-service-resource.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/5-06-corepaymentapi-autoscaling.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/18-corepaymentapi/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/19-corekekservice` (10 files)

- `03-application/01-aws-ecs-service/19-corekekservice/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/19-corekekservice/1-versions.tf`
- `03-application/01-aws-ecs-service/19-corekekservice/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/19-corekekservice/3-local-values.tf`
- `03-application/01-aws-ecs-service/19-corekekservice/5-01-corekekservice-variables.tf`
- `03-application/01-aws-ecs-service/19-corekekservice/5-04-corekekservice-taskdefinition.tf`
- `03-application/01-aws-ecs-service/19-corekekservice/5-05-corekekservice-service-resource.tf`
- `03-application/01-aws-ecs-service/19-corekekservice/5-06-corekekservice-autoscaling.tf`
- `03-application/01-aws-ecs-service/19-corekekservice/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/19-corekekservice/6-02-apigateway-resources.tf`

## `03-application/01-aws-ecs-service/20-omstaxationfacade` (11 files)

- `03-application/01-aws-ecs-service/20-omstaxationfacade/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/20-omstaxationfacade/1-versions.tf`
- `03-application/01-aws-ecs-service/20-omstaxationfacade/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/20-omstaxationfacade/3-local-values.tf`
- `03-application/01-aws-ecs-service/20-omstaxationfacade/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/20-omstaxationfacade/5-01-omstaxation-variables.tf`
- `03-application/01-aws-ecs-service/20-omstaxationfacade/5-04-omstaxation-taskdefinition.tf`
- `03-application/01-aws-ecs-service/20-omstaxationfacade/5-05-omstaxation-service-resource.tf`
- `03-application/01-aws-ecs-service/20-omstaxationfacade/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/20-omstaxationfacade/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/20-omstaxationfacade/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/21-omstaxation` (12 files)

- `03-application/01-aws-ecs-service/21-omstaxation/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/1-versions.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/3-local-values.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/5-01-omstaxation-variables.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/5-02-omstaxation-alb-resources.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/5-04-omstaxation-taskdefinition.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/5-05-omstaxation-service-resource.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/21-omstaxation/7-01-route53-dnsregistration.tf`

## `03-application/01-aws-ecs-service/22-servicemanagerscheduler` (14 files)

- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/0-terraform-remote-state-datasource.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/1-versions.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/2-generic-variables.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/3-local-values.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/4-01-datasource-parameterstore.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/5-01-servicemanagerscheduler-variables.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/5-02-servicemanagerscheduler-alb-resources.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/5-04-servicemanagerscheduler-taskdefinition.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/5-05-servicemanagerscheduler-service-resource.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/5-06-servicemanagerscheduler-iam.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/6-01-apigateway-variable.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/6-02-apigateway-resources.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/7-01-route53-dnsregistration.tf`
- `03-application/01-aws-ecs-service/22-servicemanagerscheduler/8-eventbridge-scheduler-checks.tf`

## `03-application/02-aws-lambda` (15 files)

- `03-application/02-aws-lambda/0-terraform-remote-state-datasource.tf`
- `03-application/02-aws-lambda/1-versions.tf`
- `03-application/02-aws-lambda/10-lambda-cloudwatch-event-rule.tf`
- `03-application/02-aws-lambda/11-lambda-url.tf`
- `03-application/02-aws-lambda/12-lambda-output.tf`
- `03-application/02-aws-lambda/13-parameterstore-resource.tf`
- `03-application/02-aws-lambda/14-lambda-log-metric-alarm.tf`
- `03-application/02-aws-lambda/2-generic-variables.tf`
- `03-application/02-aws-lambda/3-local-values.tf`
- `03-application/02-aws-lambda/4-datasource-parameterstore.tf`
- `03-application/02-aws-lambda/5-lambda-variables.tf`
- `03-application/02-aws-lambda/6-datasource-s3bucket.tf`
- `03-application/02-aws-lambda/7-lambda-code-s3-creation.tf`
- `03-application/02-aws-lambda/8-iam-roles-policy-resources.tf`
- `03-application/02-aws-lambda/9-lambda-resource.tf`

## `03-application/03-aws-batch-job/01-sql-job` (9 files)

- `03-application/03-aws-batch-job/01-sql-job/0-terraform-remote-state-datasource.tf`
- `03-application/03-aws-batch-job/01-sql-job/1-versions.tf`
- `03-application/03-aws-batch-job/01-sql-job/2-generic-variables.tf`
- `03-application/03-aws-batch-job/01-sql-job/3-local-values.tf`
- `03-application/03-aws-batch-job/01-sql-job/4-datasource-parameterstore.tf`
- `03-application/03-aws-batch-job/01-sql-job/5-parameterstore-resource.tf`
- `03-application/03-aws-batch-job/01-sql-job/6-01-job-variables.tf`
- `03-application/03-aws-batch-job/01-sql-job/6-02-job-definition.tf`
- `03-application/03-aws-batch-job/01-sql-job/6-03-job-event-rule.tf`

## `03-application/03-aws-batch-job/02-servicemanager-scheduled-job` (14 files)

- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/0-terraform-remote-state-datasource.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/1-versions.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/10-batch-catalog-postgres.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/11-batch-job-metadata-ssm.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/12-batch-db-connectionstring-ssm.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/13-outputs.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/2-generic-variables.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/3-local-values.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/4-batch-variables.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/5-batch-platform-lookup.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/5-datasource-db-parameterstore.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/6-iam-batch-job-role.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/9-batch-job-cloudwatch.tf`
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/9-batch-job-definition.tf`

## `03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db` (8 files)

- `03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db/1-versions.tf`
- `03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db/2-variables.tf`
- `03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db/3-local-values.tf`
- `03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db/4-datasource-parameterstore.tf`
- `03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db/5-datasource-remote-state.tf`
- `03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db/6-render-catalog-sql.tf`
- `03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db/9-outputs.tf`
- `03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db/Main.tf`

## `03-application/04-oms-providers/common/aws-api-gateway` (7 files)

- `03-application/04-oms-providers/common/aws-api-gateway/0-terraform-remote-state-datasource.tf`
- `03-application/04-oms-providers/common/aws-api-gateway/1-versions.tf`
- `03-application/04-oms-providers/common/aws-api-gateway/2-generic-variables.tf`
- `03-application/04-oms-providers/common/aws-api-gateway/3-local-values.tf`
- `03-application/04-oms-providers/common/aws-api-gateway/4-iam-roles-policy-resources.tf`
- `03-application/04-oms-providers/common/aws-api-gateway/5-apigateway-variables.tf`
- `03-application/04-oms-providers/common/aws-api-gateway/aws-api-gateway.tf`

## `03-application/04-oms-providers/common/aws-step-function` (7 files)

- `03-application/04-oms-providers/common/aws-step-function/0-terraform-remote-state-datasource.tf`
- `03-application/04-oms-providers/common/aws-step-function/1-versions.tf`
- `03-application/04-oms-providers/common/aws-step-function/2-generic-variables.tf`
- `03-application/04-oms-providers/common/aws-step-function/3-local-values.tf`
- `03-application/04-oms-providers/common/aws-step-function/4-state-machine-variables.tf`
- `03-application/04-oms-providers/common/aws-step-function/5-iam-roles-policy-resources.tf`
- `03-application/04-oms-providers/common/aws-step-function/6-aws-step-function.tf`

## `03-application/04-oms-providers/common/lambda-layers` (4 files)

- `03-application/04-oms-providers/common/lambda-layers/1-versions.tf`
- `03-application/04-oms-providers/common/lambda-layers/2-generic-variables.tf`
- `03-application/04-oms-providers/common/lambda-layers/3-layer-variables.tf`
- `03-application/04-oms-providers/common/lambda-layers/4-layer-resource.tf`

## `03-application/04-oms-providers/common/parameter-store-vars` (6 files)

- `03-application/04-oms-providers/common/parameter-store-vars/0-terraform-remote-state-datasource.tf`
- `03-application/04-oms-providers/common/parameter-store-vars/1-versions.tf`
- `03-application/04-oms-providers/common/parameter-store-vars/2-generic-variables.tf`
- `03-application/04-oms-providers/common/parameter-store-vars/3-local-values.tf`
- `03-application/04-oms-providers/common/parameter-store-vars/4-01-parameterstore-variables.tf`
- `03-application/04-oms-providers/common/parameter-store-vars/4-02-parameterstore-resource.tf`

## `03-application/04-oms-providers/lambda` (12 files)

- `03-application/04-oms-providers/lambda/0-terraform-remote-state-datasource.tf`
- `03-application/04-oms-providers/lambda/1-versions.tf`
- `03-application/04-oms-providers/lambda/10-lambda-output.tf`
- `03-application/04-oms-providers/lambda/2-generic-variables.tf`
- `03-application/04-oms-providers/lambda/3-local-values.tf`
- `03-application/04-oms-providers/lambda/3.1-parameterstore-resource.tf`
- `03-application/04-oms-providers/lambda/4-01-parameterstore-variables.tf`
- `03-application/04-oms-providers/lambda/4-datasource-parameterstore.tf`
- `03-application/04-oms-providers/lambda/5-lambda-variables.tf`
- `03-application/04-oms-providers/lambda/6-datasource-s3bucket.tf`
- `03-application/04-oms-providers/lambda/8-iam-roles-policy-resources.tf`
- `03-application/04-oms-providers/lambda/9-lambda-resource.tf`

## `03-application/05-aws-cognito` (11 files)

- `03-application/05-aws-cognito/1-versions.tf`
- `03-application/05-aws-cognito/2-variables.tf`
- `03-application/05-aws-cognito/3-main.tf`
- `03-application/05-aws-cognito/4-outputs.tf`
- `03-application/05-aws-cognito/modules/1-cognito/0-terraform-remote-state-datasource.tf`
- `03-application/05-aws-cognito/modules/1-cognito/1-local-values.tf`
- `03-application/05-aws-cognito/modules/1-cognito/3-01-cognito-variables.tf`
- `03-application/05-aws-cognito/modules/1-cognito/3-02-cognito-main.tf`
- `03-application/05-aws-cognito/modules/1-cognito/3-03-cognito-output.tf`
- `03-application/05-aws-cognito/modules/1-cognito/3-04-iam-roles-policy-resources.tf`
- `03-application/05-aws-cognito/modules/1-cognito/4-01-parameter-resources.tf`

## `03-application/06-aws-stepfunction` (27 files)

- `03-application/06-aws-stepfunction/05-workflow-batch-orchestration-checks.tf`
- `03-application/06-aws-stepfunction/1-local-values.tf`
- `03-application/06-aws-stepfunction/1-versions.tf`
- `03-application/06-aws-stepfunction/2-generic-variables.tf`
- `03-application/06-aws-stepfunction/3.main.tf`
- `03-application/06-aws-stepfunction/4.outputs.tf`
- `03-application/06-aws-stepfunction/modules/02-simfa-inbound/0-terraform-remote-state-datasource.tf`
- `03-application/06-aws-stepfunction/modules/02-simfa-inbound/1-local-values.tf`
- `03-application/06-aws-stepfunction/modules/02-simfa-inbound/2-state-machine-variables.tf`
- `03-application/06-aws-stepfunction/modules/02-simfa-inbound/3-iam-roles-policy-resources.tf`
- `03-application/06-aws-stepfunction/modules/02-simfa-inbound/4-aws-step-function.tf`
- `03-application/06-aws-stepfunction/modules/03-cybersource/0-terraform-remote-state-datasource.tf`
- `03-application/06-aws-stepfunction/modules/03-cybersource/1-local-values.tf`
- `03-application/06-aws-stepfunction/modules/03-cybersource/2-state-machine-variables.tf`
- `03-application/06-aws-stepfunction/modules/03-cybersource/3-iam-roles-policy-resources.tf`
- `03-application/06-aws-stepfunction/modules/03-cybersource/4-aws-step-function.tf`
- `03-application/06-aws-stepfunction/modules/04-paypal/0-terraform-remote-state-datasource.tf`
- `03-application/06-aws-stepfunction/modules/04-paypal/1-local-values.tf`
- `03-application/06-aws-stepfunction/modules/04-paypal/2-state-machine-variables.tf`
- `03-application/06-aws-stepfunction/modules/04-paypal/3-iam-roles-policy-resources.tf`
- `03-application/06-aws-stepfunction/modules/04-paypal/4-aws-step-function.tf`
- `03-application/06-aws-stepfunction/modules/05-workflow-batch-orchestration/checks.tf`
- `03-application/06-aws-stepfunction/modules/05-workflow-batch-orchestration/local-values.tf`
- `03-application/06-aws-stepfunction/modules/05-workflow-batch-orchestration/main.tf`
- `03-application/06-aws-stepfunction/modules/05-workflow-batch-orchestration/outputs.tf`
- `03-application/06-aws-stepfunction/modules/05-workflow-batch-orchestration/variables.tf`
- `03-application/06-aws-stepfunction/modules/05-workflow-batch-orchestration/versions.tf`

## `03-application/07-aws-sqs` (7 files)

- `03-application/07-aws-sqs/0-terraform-remote-state-datasource.tf`
- `03-application/07-aws-sqs/1-versions.tf`
- `03-application/07-aws-sqs/2-generic-variables.tf`
- `03-application/07-aws-sqs/3-local-values.tf`
- `03-application/07-aws-sqs/4-sqs-variables.tf`
- `03-application/07-aws-sqs/5-aws-sqs.tf`
- `03-application/07-aws-sqs/6-iam-roles-policy-resource.tf`

## `03-application/08-aws-event-bridge-pipes` (16 files)

- `03-application/08-aws-event-bridge-pipes/1-versions.tf`
- `03-application/08-aws-event-bridge-pipes/2-generic-variables.tf`
- `03-application/08-aws-event-bridge-pipes/3.main.tf`
- `03-application/08-aws-event-bridge-pipes/4.outputs.tf`
- `03-application/08-aws-event-bridge-pipes/modules/01-sqs/0-terraform-remote-state-datasource.tf`
- `03-application/08-aws-event-bridge-pipes/modules/01-sqs/2-generic-variables.tf`
- `03-application/08-aws-event-bridge-pipes/modules/01-sqs/3-local-values.tf`
- `03-application/08-aws-event-bridge-pipes/modules/01-sqs/4-pipes-variables.tf`
- `03-application/08-aws-event-bridge-pipes/modules/01-sqs/5.iam-roles-policy-resource.tf`
- `03-application/08-aws-event-bridge-pipes/modules/01-sqs/6-aws-event-bridge-pipes.tf`
- `03-application/08-aws-event-bridge-pipes/modules/02-dlq/0-terraform-remote-state-datasource.tf`
- `03-application/08-aws-event-bridge-pipes/modules/02-dlq/2-generic-variables.tf`
- `03-application/08-aws-event-bridge-pipes/modules/02-dlq/3-local-values.tf`
- `03-application/08-aws-event-bridge-pipes/modules/02-dlq/4-pipes-variables.tf`
- `03-application/08-aws-event-bridge-pipes/modules/02-dlq/5.iam-roles-policy-resource.tf`
- `03-application/08-aws-event-bridge-pipes/modules/02-dlq/6-aws-event-bridge-pipes.tf`

## `03-application/09-aws-eventbus` (8 files)

- `03-application/09-aws-eventbus/0-terraform-remote-state-datasource.tf`
- `03-application/09-aws-eventbus/1-versions.tf`
- `03-application/09-aws-eventbus/2-generic-variables.tf`
- `03-application/09-aws-eventbus/3-local-values.tf`
- `03-application/09-aws-eventbus/4-eventbus-variable.tf`
- `03-application/09-aws-eventbus/5-eventbus-resource.tf`
- `03-application/09-aws-eventbus/6-event-rule-target.tf`
- `03-application/09-aws-eventbus/7-eventbus-roles-policy.tf`

## `03-application/10-aws-api-gateway` (12 files)

- `03-application/10-aws-api-gateway/1-versions.tf`
- `03-application/10-aws-api-gateway/2-generic-variables.tf`
- `03-application/10-aws-api-gateway/3-service-quota-api-gateway.tf`
- `03-application/10-aws-api-gateway/4-iam-common-roles-policy-resources.tf`
- `03-application/10-aws-api-gateway/5-main.tf`
- `03-application/10-aws-api-gateway/6-outputs.tf`
- `03-application/10-aws-api-gateway/modules/01-payment/0-terraform-remote-state-datasource.tf`
- `03-application/10-aws-api-gateway/modules/01-payment/2-provider-variables.tf`
- `03-application/10-aws-api-gateway/modules/01-payment/3-local-values.tf`
- `03-application/10-aws-api-gateway/modules/01-payment/4-iam-roles-policy-resources.tf`
- `03-application/10-aws-api-gateway/modules/01-payment/5-apigateway-variables.tf`
- `03-application/10-aws-api-gateway/modules/01-payment/aws-api-gateway.tf`

## `03-application/10-aws-dlq` (5 files)

- `03-application/10-aws-dlq/1-versions.tf`
- `03-application/10-aws-dlq/2-generic-variables.tf`
- `03-application/10-aws-dlq/3-local-values.tf`
- `03-application/10-aws-dlq/4-dlq-variables.tf`
- `03-application/10-aws-dlq/5-aws-dlq.tf`

## `03-application/11-aws-parameterstore` (6 files)

- `03-application/11-aws-parameterstore/0-terraform-remote-state-datasource.tf`
- `03-application/11-aws-parameterstore/1-versions.tf`
- `03-application/11-aws-parameterstore/2-generic-variables.tf`
- `03-application/11-aws-parameterstore/3-local-values.tf`
- `03-application/11-aws-parameterstore/4-01-parameterstore-variables.tf`
- `03-application/11-aws-parameterstore/4-02-parameterstore-resource.tf`

## `03-application/12-core-route53` (5 files)

- `03-application/12-core-route53/1-versions.tf`
- `03-application/12-core-route53/2-generic-variables.tf`
- `03-application/12-core-route53/3-local-values.tf`
- `03-application/12-core-route53/4-01-datasource-parameterstore.tf`
- `03-application/12-core-route53/5-01-route53-dnsregistration.tf`

## `03-application/13-snowflake/01-dms-setup` (12 files)

- `03-application/13-snowflake/01-dms-setup/00-terraform-remote-state-datasource.tf`
- `03-application/13-snowflake/01-dms-setup/01-providers.tf`
- `03-application/13-snowflake/01-dms-setup/02-variables.tf`
- `03-application/13-snowflake/01-dms-setup/03-local-values.tf`
- `03-application/13-snowflake/01-dms-setup/04-vpc-gateway-endpoint.tf`
- `03-application/13-snowflake/01-dms-setup/05-s3-resource.tf`
- `03-application/13-snowflake/01-dms-setup/06-dms-role.tf`
- `03-application/13-snowflake/01-dms-setup/07-dms-instance.tf`
- `03-application/13-snowflake/01-dms-setup/08-dms-source-endpoint.tf`
- `03-application/13-snowflake/01-dms-setup/09-dms-target-endpoint.tf`
- `03-application/13-snowflake/01-dms-setup/10-dms-replication-task.tf`
- `03-application/13-snowflake/01-dms-setup/11-outputs.tf`

## `03-application/13-snowflake/02-snowflake-setup` (22 files)

- `03-application/13-snowflake/02-snowflake-setup/00-terraform-remote-state-datasource.tf`
- `03-application/13-snowflake/02-snowflake-setup/01-providers.tf`
- `03-application/13-snowflake/02-snowflake-setup/02-variables.tf`
- `03-application/13-snowflake/02-snowflake-setup/03-local-values.tf`
- `03-application/13-snowflake/02-snowflake-setup/06-snowflake-schema.tf`
- `03-application/13-snowflake/02-snowflake-setup/07-snowflake-external-stage-integration.tf`
- `03-application/13-snowflake/02-snowflake-setup/08-snowflake-file-format-parquet.tf`
- `03-application/13-snowflake/02-snowflake-setup/09-snowflake-stage.tf`
- `03-application/13-snowflake/02-snowflake-setup/10-snowflake-tables.tf`
- `03-application/13-snowflake/02-snowflake-setup/11-snowflake-pipe-creation.tf`
- `03-application/13-snowflake/02-snowflake-setup/12-snowflake-table-oms-raw-table-merge-etl-log.tf`
- `03-application/13-snowflake/02-snowflake-setup/13-snowflake-procedure-oms-get-merge-query.tf`
- `03-application/13-snowflake/02-snowflake-setup/14-snowflake-procedure-oms-raw-table-merge-etl.tf`
- `03-application/13-snowflake/02-snowflake-setup/15-snowflake-stream.tf`
- `03-application/13-snowflake/02-snowflake-setup/16-snowflake-task.tf`
- `03-application/13-snowflake/02-snowflake-setup/17-snowflake-taskstatusupdate.tf`
- `03-application/13-snowflake/02-snowflake-setup/18-snowflake-mutuable-tables.tf`
- `03-application/13-snowflake/02-snowflake-setup/19-snowflake-stage-tables.tf`
- `03-application/13-snowflake/02-snowflake-setup/20-snowflake-alter-tables.tf`
- `03-application/13-snowflake/02-snowflake-setup/21-snowflake-procedure-oms-purge-staging-tables.tf`
- `03-application/13-snowflake/02-snowflake-setup/22-snowflake-purge-task.tf`
- `03-application/13-snowflake/02-snowflake-setup/23-snowflake-purge-taskstatusupdate.tf`

## 01-infrastructure/06-database-operation (bastion SQL bootstrap) (15 files)

- `01-infrastructure/06-database-operation/01-rds-init/Main.tf`
- `01-infrastructure/06-database-operation/01-rds-init/datasource-parameterstore-master.tf`
- `01-infrastructure/06-database-operation/01-rds-init/datasource-parameterstore.tf`
- `01-infrastructure/06-database-operation/01-rds-init/db-cleanup-v1-1/Main.tf`
- `01-infrastructure/06-database-operation/01-rds-init/db-cleanup-v1-1/variables.tf`
- `01-infrastructure/06-database-operation/01-rds-init/initdb-metadata/Main.tf`
- `01-infrastructure/06-database-operation/01-rds-init/initdb-metadata/datasource-parameterstore.tf`
- `01-infrastructure/06-database-operation/01-rds-init/initdb-metadata/variables.tf`
- `01-infrastructure/06-database-operation/01-rds-init/initdb-post-v1-1/Main.tf`
- `01-infrastructure/06-database-operation/01-rds-init/initdb-post-v1-1/variables.tf`
- `01-infrastructure/06-database-operation/01-rds-init/initdb-post-v1-2/Main.tf`
- `01-infrastructure/06-database-operation/01-rds-init/initdb-post-v1-2/variables.tf`
- `01-infrastructure/06-database-operation/01-rds-init/initdb-post-v1-3/Main.tf`
- `01-infrastructure/06-database-operation/01-rds-init/initdb-post-v1-3/variables.tf`
- `01-infrastructure/06-database-operation/01-rds-init/variables.tf`

## 01-infrastructure/08-core (legacy modules & eom-terraform-master) (356 files)

- `01-infrastructure/08-core/DMS/hoxleigh-uat/01-rds-init/Main.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/01-rds-init/variables.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/0_DMS_prerequisite_roles/main.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/0_DMS_prerequisite_roles/providers.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/1_clientdb/main.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/1_clientdb/outputs.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/1_clientdb/providers.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/1_clientdb/variables.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/2_shopvisible/main.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/2_shopvisible/outputs.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/2_shopvisible/providers.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/2_shopvisible/variables.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/3_toronando/main.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/3_toronando/outputs.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/3_toronando/providers.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/3_toronando/variables.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/4_toronando_non_cdc/main.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/4_toronando_non_cdc/outputs.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/4_toronando_non_cdc/providers.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/4_toronando_non_cdc/variables.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/5_eom_service_fulfillment/main.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/5_eom_service_fulfillment/outputs.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/5_eom_service_fulfillment/providers.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/5_eom_service_fulfillment/variables.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/6_eom_service_order_adapter/main.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/6_eom_service_order_adapter/outputs.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/6_eom_service_order_adapter/providers.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/6_eom_service_order_adapter/variables.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/7_keycloak/main.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/7_keycloak/outputs.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/7_keycloak/providers.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/7_keycloak/variables.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/8_scheduler/main.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/8_scheduler/outputs.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/8_scheduler/providers.tf`
- `01-infrastructure/08-core/DMS/hoxleigh-uat/TerraformScript/DMS_OMS/QaDB/8_scheduler/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/PerformanceDB/Main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/clientdb/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/clientdb/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/clientdb/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/clientdb/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/eom_service_fulfillment/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/eom_service_fulfillment/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/eom_service_fulfillment/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/eom_service_fulfillment/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/eom_service_order_adapter/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/eom_service_order_adapter/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/eom_service_order_adapter/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/eom_service_order_adapter/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/keycloak/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/keycloak/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/keycloak/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/scheduler/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/scheduler/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/scheduler/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/scheduler/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/shopvisible/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/shopvisible/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/shopvisible/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/shopvisible/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/toronando/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/toronando/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/toronando/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/DMS_OMS/QaDB/toronando/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/RDS_Auroroa_Postgres_Serverless/qa/RDS_Create/Main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/RDS_Auroroa_Postgres_Serverless/qa/RDS_Create/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/RDS_Auroroa_Postgres_Serverless/qa/RDS_Init/Main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript/RDS_Auroroa_Postgres_Serverless/qa/RDS_Init/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/PerformanceDB/Main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/clientdb/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/clientdb/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/clientdb/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/clientdb/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/eom_service_fulfillment/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/eom_service_fulfillment/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/eom_service_fulfillment/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/eom_service_fulfillment/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/eom_service_order_adapter/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/eom_service_order_adapter/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/eom_service_order_adapter/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/eom_service_order_adapter/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/keycloak/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/keycloak/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/keycloak/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/keycloak/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/scheduler/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/scheduler/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/scheduler/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/scheduler/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/shopvisible/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/shopvisible/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/shopvisible/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/shopvisible/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/toronando/main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/toronando/outputs.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/toronando/providers.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/DMS_OMS/QaDB/toronando/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/RDS_Auroroa_Postgres_Serverless/qa/RDS_Create/Main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/RDS_Auroroa_Postgres_Serverless/qa/RDS_Create/variables.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/RDS_Auroroa_Postgres_Serverless/qa/RDS_Init/Main.tf`
- `01-infrastructure/08-core/DMS/windsor-uat/TerraformScript_run2/RDS_Auroroa_Postgres_Serverless/qa/RDS_Init/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_asg/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_asg/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_asg/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_asg/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_lc/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_lc/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_lc/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_lc/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_lt/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_lt/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_lt/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_api_lt/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_app-old/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_app-old/output.tf`
- `01-infrastructure/08-core/modules/eom/eom_app-old/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_app-old/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_app/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_app/output.tf`
- `01-infrastructure/08-core/modules/eom/eom_app/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_app/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_asg_launch_config/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_asg_launch_config/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_content-old/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_content-old/output.tf`
- `01-infrastructure/08-core/modules/eom/eom_content-old/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_content-old/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_content/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_content/output.tf`
- `01-infrastructure/08-core/modules/eom/eom_content/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_content/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_lambda_package/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_lambda_package/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb_lambda/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb_lambda/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb_lambda/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb_lambda/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb_static_ips/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb_static_ips/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb_static_ips/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_nlb_static_ips/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_s3_buckets/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_s3_buckets/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_s3_buckets/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_services/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_services/output.tf`
- `01-infrastructure/08-core/modules/eom/eom_services/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_services/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_services_alb/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_services_alb/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_services_alb/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_services_alb/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_sftp/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_sftp/output.tf`
- `01-infrastructure/08-core/modules/eom/eom_sftp/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_sftp/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_asg/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_asg/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_asg/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_asg/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_lc/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_lc/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_lc/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_lc/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_lt/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_lt/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_lt/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_sitemanager_lt/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_sqlserver/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_sqlserver/output.tf`
- `01-infrastructure/08-core/modules/eom/eom_sqlserver/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_sqlserver/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_sqlserver_micro/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_sqlserver_micro/output.tf`
- `01-infrastructure/08-core/modules/eom/eom_sqlserver_micro/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_sqlserver_micro/versions.tf`
- `01-infrastructure/08-core/modules/eom/eom_web_api_nlb_static_ips/main.tf`
- `01-infrastructure/08-core/modules/eom/eom_web_api_nlb_static_ips/outputs.tf`
- `01-infrastructure/08-core/modules/eom/eom_web_api_nlb_static_ips/variables.tf`
- `01-infrastructure/08-core/modules/eom/eom_web_api_nlb_static_ips/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-route53/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-route53/outputs.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-route53/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-route53/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-vpc-dual-zone/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-vpc-dual-zone/outputs.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-vpc-dual-zone/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-vpc-dual-zone/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-vpc/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-vpc/outputs.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-vpc/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/eks-vpc/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_dc_primary/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_dc_primary/output.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_dc_primary/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_dc_primary/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_dc_secondary/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_dc_secondary/output.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_dc_secondary/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_dc_secondary/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_groups/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_groups/outputs.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_groups/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_groups/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_mgmt_groups/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_mgmt_groups/outputs.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_mgmt_groups/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_mgmt_groups/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_mgmt_vpc/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_mgmt_vpc/outputs.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_mgmt_vpc/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_mgmt_vpc/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_openvpn/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_openvpn/output.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_openvpn/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_openvpn/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_vpc/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_vpc/outputs.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_vpc/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/eom_vpc/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/lambda_sns/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/lambda_sns/outputs.tf`
- `01-infrastructure/08-core/modules/infrastructure/lambda_sns/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/lambda_sns/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/oms_iam/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/oms_iam/outputs.tf`
- `01-infrastructure/08-core/modules/infrastructure/oms_iam/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/oms_iam/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/tf_state_dynamodb/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/tf_state_dynamodb/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/tf_state_dynamodb/versions.tf`
- `01-infrastructure/08-core/modules/infrastructure/tf_state_s3/main.tf`
- `01-infrastructure/08-core/modules/infrastructure/tf_state_s3/outputs.tf`
- `01-infrastructure/08-core/modules/infrastructure/tf_state_s3/variables.tf`
- `01-infrastructure/08-core/modules/infrastructure/tf_state_s3/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/iam/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/iam/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/iam/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/iam/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/iam/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/oms_2_iam/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/oms_2_iam/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/oms_2_iam/ouputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/oms_2_iam/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/s3_logs/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/s3_logs/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/s3_logs/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/s3_logs/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/ssm_destroy/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/ssm_destroy/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/ssm_destroy/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/ssm_destroy/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/ssm_destroy/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/ssm_launch/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/ssm_launch/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/ssm_launch/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/ssm_launch/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/ssm_launch/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/tf_state_dynamodb/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/tf_state_dynamodb/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/tf_state_s3/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/account/tf_state_s3/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/api_nlb_static_ips/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/api_nlb_static_ips/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/api_nlb_static_ips/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/api_nlb_static_ips/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/api_nlb_static_ips/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/apiserver_asg/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/apiserver_asg/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/apiserver_asg/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/apiserver_asg/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/apiserver_asg/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/apiserver_lc/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/apiserver_lc/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/apiserver_lc/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/apiserver_lc/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/apiserver_lc/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/app/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/app/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/app/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/app/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/app/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/asg_launch_config/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/asg_launch_config/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/asg_launch_config/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/content/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/content/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/content/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/content/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/content/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/dhcp-options-set/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/dhcp-options-set/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/dhcp-options-set/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/dhcp-options-set/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/groups/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/groups/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/groups/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/groups/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/groups/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/nlb/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/nlb/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/nlb/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/nlb/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/nlb/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/services/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/services/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/services/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/services/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/services/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/services_alb/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/services_alb/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/services_alb/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/services_alb/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/services_alb/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sftp/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sftp/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sftp/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sftp/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sftp/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sftp_nlb_static_ips/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sftp_nlb_static_ips/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sftp_nlb_static_ips/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sftp_nlb_static_ips/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sftp_nlb_static_ips/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_asg/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_asg/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_asg/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_asg/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_asg/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_lc/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_lc/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_lc/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_lc/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_lc/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_nlb_static_ips/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_nlb_static_ips/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_nlb_static_ips/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_nlb_static_ips/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sitemanager_nlb_static_ips/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sqlserver/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sqlserver/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sqlserver/outputs.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sqlserver/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/sqlserver/versions.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/transitgateway_attachment/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/transitgateway_attachment/transitgateway-association.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/transitgateway_attachment/transitgateway-variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/vpc/config.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/vpc/main.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/vpc/output.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/vpc/variables.tf`
- `01-infrastructure/08-core/projects/eom-terraform-master/vpc/versions.tf`
