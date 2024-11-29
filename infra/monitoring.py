import pulumi
import pulumi_aws as aws
from pulumi import export, Config, Output
import json

# Dynamically import outputs from network and compute modules
from infra import network
from infra import compute

# Retrieve network outputs
vpc_id = network.vpc_id
public_subnets = network.public_subnets  # Ensure this is defined in network.py
private_subnets = network.private_subnets

# Retrieve compute outputs
alb_dns_name = compute.alb_dns_name
ecs_cluster_id = compute.ecs_cluster_id
alb_listener_arn = compute.alb_listener_arn
ecs_task_sg_id = compute.ecs_task_sg_id

# Pulumi Configurations
config = Config()
key_name = config.require("key_name")  # SSH Key Pair name
instance_type = config.get("instance_type") or "t2.medium"  # Default instance type
ami_id = config.get("ami_id") or "ami-0c02fb55956c7d316"  # Amazon Linux 2 AMI
tags = {"Environment": "dev", "Project": "monitoring-layer"}

# Security Group for ELK Stack
elk_sg = aws.ec2.SecurityGroup(
    "elkSecurityGroup",
    vpc_id=vpc_id,
    description="Allow access to ELK stack services",
    ingress=[
        # Allow SSH access from anywhere
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
        ),
        # Allow Kibana access from ALB
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5601,
            to_port=5601,
            cidr_blocks=["0.0.0.0/0"],  # Adjust for tighter security
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={**tags, "Name": "elkSecurityGroup"},
)

# Create the IAM Role and Policy
instance_role = aws.iam.Role(
    "instanceRole",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": { "Service": "ec2.amazonaws.com" }
            }
        ]
    }""",
)

policy = aws.iam.RolePolicyAttachment(
    "s3ReadOnlyPolicy",
    role=instance_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
)

instance_profile = aws.iam.InstanceProfile("instanceProfile", role=instance_role.name)

# EC2 Instance Configuration
elk_instance = aws.ec2.Instance(
    "elkInstance",
    ami=ami_id,
    instance_type=instance_type,
    subnet_id=public_subnets[0],
    associate_public_ip_address=True,
    key_name=key_name,
    vpc_security_group_ids=[elk_sg.id],
    iam_instance_profile=instance_profile.name,
    user_data="""
    #!/bin/bash
    aws s3 cp s3://elk-monitoring-setup/setup.sh /tmp/setup.sh
    chmod +x /tmp/setup.sh
    sleep 60
    /tmp/setup.sh
    """,
    tags={**tags, "Name": "elkInstance"},
)

# Target Group for Kibana
kibana_target_group = aws.lb.TargetGroup(
    "kibanaTargetGroup",
    port=5601,
    protocol="HTTP",
    target_type="instance",
    vpc_id=vpc_id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        protocol="HTTP",
        path="/",
        interval=30,
        timeout=5,
        healthy_threshold=3,
        unhealthy_threshold=3,
    ),
    tags={**tags, "Name": "kibanaTargetGroup"},
)

# Attach Instance to Target Group
# aws.lb.TargetGroupAttachment(
#     "kibanaTargetGroupAttachment",
#     target_group_arn=kibana_target_group.arn,
#     target_id=elk_instance.id,
#     port=5601,
# )

# Add Listener Rule for Kibana
aws.lb.ListenerRule(
    "kibanaListenerRule",
    listener_arn=alb_listener_arn,
    actions=[
        aws.lb.ListenerRuleActionArgs(
            type="forward",
            target_group_arn=kibana_target_group.arn,
        )
    ],
    conditions=[
        aws.lb.ListenerRuleConditionArgs(
            path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
                values=["/kibana*"]  # Correct format for path patterns
            )
        )
    ],
    priority=10,  # Ensure no conflicts with other listener rules
)



# Outputs for Monitoring Services
export("kibana_dashboard_url", Output.concat("http://", alb_dns_name, "/kibana"))
export("elk_instance_public_ip", elk_instance.public_ip)
export("elk_instance_domain_name", elk_instance.public_dns)
