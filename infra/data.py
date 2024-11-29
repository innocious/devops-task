import pulumi
import pulumi_aws as aws
from pulumi import Config, export

# Import network outputs dynamically
from infra import network

# Access network outputs
vpc_id = network.vpc_id
private_subnets = network.private_subnets
private_sg_id = network.private_sg_id

# Pulumi configuration for RDS credentials
config = Config()
db_username = config.require("db_username")  # Fetch username securely from Pulumi config
db_password = config.require_secret("db_password")  # Fetch password securely from Pulumi config

# RDS Subnet Group
rds_subnet_group = aws.rds.SubnetGroup(
    "rdsSubnetGroup",
    name="rds_subnet_group",
    subnet_ids=private_subnets,
    tags={"Name": "rds-subnet-group"},
)

# RDS Instance
rds_instance = aws.rds.Instance(
    "postgresInstance",
    identifier="postgres-instance",
    allocated_storage=20,
    max_allocated_storage=100,
    instance_class="db.t3.micro",
    engine="postgres",
    engine_version="16.6",
    db_name="appdb",
    username=db_username,
    password=db_password,
    db_subnet_group_name=rds_subnet_group.name,
    vpc_security_group_ids=[private_sg_id],
    backup_retention_period=7,
    backup_window="04:00-05:00",
    maintenance_window="Sun:05:00-Sun:06:00",
    multi_az=False,
    storage_encrypted=True,
    skip_final_snapshot=True,
    deletion_protection=False,
    tags={"Name": "postgres-app-instance"},
)

# Export Outputs
export("rds_endpoint", rds_instance.endpoint)
export("rds_subnet_group", rds_subnet_group.name)
