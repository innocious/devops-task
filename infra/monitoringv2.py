import pulumi
import pulumi_aws as aws
from pulumi import export
import json

# Dynamically import outputs from network and compute modules
from infra import network
from infra import compute

# Retrieve network outputs
vpc_id = network.vpc_id
private_subnets = network.private_subnets

# Retrieve compute outputs
alb_dns_name = compute.alb_dns_name
ecs_cluster_id = compute.ecs_cluster_id
alb_listener_arn = compute.alb_listener_arn
ecs_task_sg_id = compute.ecs_task_sg_id

# Elasticsearch Task Definition
elasticsearch_task = aws.ecs.TaskDefinition(
    "elasticsearchTask",
    family="elasticsearch",
    cpu="1024",
    memory="2048",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    container_definitions=json.dumps([
        {
            "name": "elasticsearch",
            "image": "docker.elastic.co/elasticsearch/elasticsearch:7.17.0",
            "essential": True,
            "portMappings": [
                {"containerPort": 9200, "protocol": "tcp"},
                {"containerPort": 9300, "protocol": "tcp"},
            ],
            "environment": [
                {"name": "discovery.type", "value": "single-node"},
                {"name": "network.host", "value": "0.0.0.0"},
            ],
        }
    ]),
)

# Logstash Task Definition
logstash_task = aws.ecs.TaskDefinition(
    "logstashTask",
    family="logstash",
    cpu="512",
    memory="1024",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    container_definitions=json.dumps([
        {
            "name": "logstash",
            "image": "docker.elastic.co/logstash/logstash:7.17.0",
            "essential": True,
            "portMappings": [
                {"containerPort": 5044, "protocol": "tcp"},
                {"containerPort": 9600, "protocol": "tcp"},
            ],
        }
    ]),
)

# Kibana Task Definition
kibana_task = aws.ecs.TaskDefinition(
    "kibanaTask",
    family="kibana",
    cpu="512",
    memory="1024",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    container_definitions=json.dumps([
        {
            "name": "kibana",
            "image": "docker.elastic.co/kibana/kibana:7.17.0",
            "essential": True,
            "portMappings": [
                {"containerPort": 5601, "protocol": "tcp"},
            ],
            "environment": [
                {"name": "ELASTICSEARCH_HOSTS", "value": "http://elasticsearch:9200"},
            ],
        }
    ]),
)

# Elasticsearch Service
elasticsearch_service = aws.ecs.Service(
    "elasticsearchService",
    cluster=ecs_cluster_id,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=elasticsearch_task.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        subnets=private_subnets,
        security_groups=[ecs_task_sg_id],
    ),
)

# Logstash Service
logstash_service = aws.ecs.Service(
    "logstashService",
    cluster=ecs_cluster_id,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=logstash_task.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        subnets=private_subnets,
        security_groups=[ecs_task_sg_id],
    ),
)

# Kibana Service
kibana_service = aws.ecs.Service(
    "kibanaService",
    cluster=ecs_cluster_id,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=kibana_task.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        subnets=private_subnets,
        security_groups=[ecs_task_sg_id],
    ),
)

# Export the Kibana URL
kibana_url = alb_dns_name.apply(lambda dns_name: f"http://{dns_name}/kibana")
export("kibana_dashboard_url", kibana_url)
