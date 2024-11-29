import pulumi
import pulumi_aws as aws
import json
from pulumi import Config

# Pulumi configuration for sensitive credentials
config = Config()
db_username = config.require("db_username")  # Fetch username securely
db_password = config.require_secret("db_password")  # Fetch password securely

# Create a generic Secrets Manager secret
generic_secret = aws.secretsmanager.Secret(
    "genericSecret",
    description="A generic secret for application use",
    tags={"Environment": "dev"},
)

# Store a sample value in the Secrets Manager secret
generic_secret_value = aws.secretsmanager.SecretVersion(
    "genericSecretValue",
    secret_id=generic_secret.id,
    secret_string=json.dumps({"key": "value"}),  # Replace with actual secret data
)


# ECS Task Execution Role
ecs_task_execution_role = aws.iam.Role(
    "ecsTaskExecutionRole",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Effect": "Allow",
                "Sid": "",
            }
        ]
    }),
    tags={"Name": "ecsTaskExecutionRole"},
)

# Attach ECS Task Execution Role Policies
ecs_task_execution_policy = aws.iam.RolePolicyAttachment(
    "ecsTaskExecutionPolicy",
    role=ecs_task_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

# Export Outputs
pulumi.export("ecs_task_execution_role_arn", ecs_task_execution_role.arn)  # Export the ARN
pulumi.export("ecs_task_execution_role", ecs_task_execution_role.name)  # Export the role name (optional)

# Export the secret ARN for future use
pulumi.export("generic_secret_arn", generic_secret.arn)
# Assign `ecs_task_execution_role_arn` as a Python attribute
ecs_task_execution_role_arn = ecs_task_execution_role.arn