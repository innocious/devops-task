from pulumi import export
import pulumi_aws as aws
import json

# Import network and security outputs dynamically
from infra import network
from infra import security

# Retrieve network outputs dynamically
vpc_id = network.vpc_id
public_subnets = network.public_subnets
private_subnets = network.private_subnets
public_sg_id = network.public_sg_id

# Retrieve IAM role ARN from security.py
ecs_task_execution_role_arn = security.ecs_task_execution_role_arn

# ECS Task Security Group
ecs_task_sg = aws.ec2.SecurityGroup(
    "ecsTaskSg",
    vpc_id=vpc_id,
    description="Security group for ECS tasks",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            security_groups=[public_sg_id],  # Allow traffic from ALB security group
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",  # All protocols
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],  # Allow all outbound traffic
        )
    ],
    tags={"Name": "ecsTaskSg"},
)

# ECS Cluster
ecs_cluster = aws.ecs.Cluster(
    "appCluster",
    tags={"Name": "appCluster"}
)

# Application Load Balancer (ALB)
alb = aws.lb.LoadBalancer(
    "appAlb",
    internal=False,
    security_groups=[public_sg_id],  # Use Public SG for ALB
    subnets=public_subnets,  # Use public subnets for ALB
    load_balancer_type="application",
    tags={"Name": "appAlb"},
)

# ALB Target Group
target_group = aws.lb.TargetGroup(
    "appTargetGroup",
    port=80,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc_id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        protocol="HTTP",
        path="/",  # Default health check path for Nginx
        interval=30,
        timeout=5,
        healthy_threshold=3,
        unhealthy_threshold=3,
    ),
    tags={"Name": "appTargetGroup"},
)

# ALB Listener
alb_listener = aws.lb.Listener(
    "appAlbListener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=target_group.arn,
        )
    ],
)

# ECS Task Definition
container_definitions = json.dumps([
    {
        "name": "appContainer",
        "image": "nginx",  # Replace with your application image
        "portMappings": [
            {
                "containerPort": 80,
                "protocol": "tcp"
            }
        ]
    }
])

task_definition = aws.ecs.TaskDefinition(
    "appTask",
    family="appTaskFamily",
    cpu="256",
    memory="512", 
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=ecs_task_execution_role_arn,
    container_definitions=container_definitions,
    tags={"Name": "appTask"},
)

# ECS Service
ecs_service = aws.ecs.Service(
    "appService",
    cluster=ecs_cluster.id,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,  # Tasks remain private
        subnets=private_subnets,  # Deploy in private subnets
        security_groups=[ecs_task_sg.id],  # Use ECS Task SG
    ),
    load_balancers=[
        aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=target_group.arn,
            container_name="appContainer",
            container_port=80,
        )
    ],
    tags={"Name": "appService"},
)

# Assign outputs as Python attributes
alb_dns_name = alb.dns_name
ecs_cluster_id = ecs_cluster.id
alb_listener_arn = alb_listener.arn
ecs_task_sg_id = ecs_task_sg.id

# Export the ALB DNS Name for Testing
export("alb_dns_name", alb.dns_name)

# Export the ECS cluster ID
export("ecs_cluster_id", ecs_cluster.id)

# Export the ALB listener ARN
export("alb_listener_arn", alb_listener.arn)

# Export ECS task SG ID and private subnets
export("ecs_task_sg_id", ecs_task_sg.id)
export("private_subnets", private_subnets)
