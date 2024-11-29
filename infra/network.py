import pulumi
import pulumi_aws as aws

# Create a VPC
vpc = aws.ec2.Vpc(
    "mainVpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "mainVpc"},
)

# Public Subnets in Two AZs
public_subnet_az1 = aws.ec2.Subnet(
    "publicSubnetAz1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-west-2a",
    map_public_ip_on_launch=True,
    tags={"Name": "publicSubnetAz1"},
)

public_subnet_az2 = aws.ec2.Subnet(
    "publicSubnetAz2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-west-2b",
    map_public_ip_on_launch=True,
    tags={"Name": "publicSubnetAz2"},
)

# Private Subnets in Two AZs
private_subnet_az1 = aws.ec2.Subnet(
    "privateSubnetAz1",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone="us-west-2a",
    tags={"Name": "privateSubnetAz1"},
)

private_subnet_az2 = aws.ec2.Subnet(
    "privateSubnetAz2",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone="us-west-2b",
    tags={"Name": "privateSubnetAz2"},
)

# Internet Gateway for Public Subnets
internet_gateway = aws.ec2.InternetGateway(
    "mainIgw",
    vpc_id=vpc.id,
    tags={"Name": "mainIgw"},
)

# NAT Gateway in Public Subnet (AZ1)
eip = aws.ec2.Eip("natEip", tags={"Name": "natEip"})
# nat_gateway = aws.ec2.NatGateway(
#     "natGateway",
#     allocation_id=eip.id,
#     subnet_id=public_subnet_az1.id,
#     tags={"Name": "natGateway"},
# )

# Public Route Table
public_route_table = aws.ec2.RouteTable(
    "publicRouteTable",
    vpc_id=vpc.id,
    routes=[
        {"cidr_block": "0.0.0.0/0", "gateway_id": internet_gateway.id},
    ],
    tags={"Name": "publicRouteTable"},
)

# Associate Public Subnets with Public Route Table
aws.ec2.RouteTableAssociation(
    "publicRouteTableAssocAz1",
    subnet_id=public_subnet_az1.id,
    route_table_id=public_route_table.id,
)

aws.ec2.RouteTableAssociation(
    "publicRouteTableAssocAz2",
    subnet_id=public_subnet_az2.id,
    route_table_id=public_route_table.id,
)

# Private Route Table
# private_route_table = aws.ec2.RouteTable(
#     "privateRouteTable",
#     vpc_id=vpc.id,
#     routes=[
#         {"cidr_block": "0.0.0.0/0", "nat_gateway_id": nat_gateway.id},
#     ],
#     tags={"Name": "privateRouteTable"},
# )

# Associate Private Subnets with Private Route Table
# aws.ec2.RouteTableAssociation(
#     "privateRouteTableAssocAz1",
#     subnet_id=private_subnet_az1.id,
#     route_table_id=private_route_table.id,
# )

# aws.ec2.RouteTableAssociation(
#     "privateRouteTableAssocAz2",
#     subnet_id=private_subnet_az2.id,
#     route_table_id=private_route_table.id,
# )

# Security Group for Public Resources
public_sg = aws.ec2.SecurityGroup(
    "publicSg",
    vpc_id=vpc.id,
    description="Security group for public-facing resources",
    ingress=[
        {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 443, "to_port": 443, "cidr_blocks": ["0.0.0.0/0"]},
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ],
    tags={"Name": "publicSg"},
)

# Security Group for Private Resources
private_sg = aws.ec2.SecurityGroup(
    "privateSg",
    vpc_id=vpc.id,
    description="Security group for private resources",
    ingress=[
        {"protocol": "tcp", "from_port": 5432, "to_port": 5432, "cidr_blocks": ["10.0.0.0/16"]},
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ],
    tags={"Name": "privateSg"},
)

# VPC Endpoints
rds_endpoint = aws.ec2.VpcEndpoint(
    "rdsEndpoint",
    vpc_id=vpc.id,
    service_name=f"com.amazonaws.{aws.config.region}.rds",
    subnet_ids=[private_subnet_az1.id, private_subnet_az2.id],
    security_group_ids=[private_sg.id],
    vpc_endpoint_type="Interface",
    tags={"Name": "rdsEndpoint"},
)

ecs_endpoint = aws.ec2.VpcEndpoint(
    "ecsEndpoint",
    vpc_id=vpc.id,
    service_name=f"com.amazonaws.{aws.config.region}.ecs",
    subnet_ids=[private_subnet_az1.id, private_subnet_az2.id],
    security_group_ids=[private_sg.id],
    vpc_endpoint_type="Interface",
    tags={"Name": "ecsEndpoint"},
)

ecs_agent_endpoint = aws.ec2.VpcEndpoint(
    "ecsAgentEndpoint",
    vpc_id=vpc.id,
    service_name=f"com.amazonaws.{aws.config.region}.ecs-agent",
    subnet_ids=[private_subnet_az1.id, private_subnet_az2.id],
    security_group_ids=[private_sg.id],
    vpc_endpoint_type="Interface",
    tags={"Name": "ecsAgentEndpoint"},
)

ecs_telemetry_endpoint = aws.ec2.VpcEndpoint(
    "ecsTelemetryEndpoint",
    vpc_id=vpc.id,
    service_name=f"com.amazonaws.{aws.config.region}.ecs-telemetry",
    subnet_ids=[private_subnet_az1.id, private_subnet_az2.id],
    security_group_ids=[private_sg.id],
    vpc_endpoint_type="Interface",
    tags={"Name": "ecsTelemetryEndpoint"},
)

# Make outputs accessible as Python variables
vpc_id = vpc.id
public_subnets = [public_subnet_az1.id, public_subnet_az2.id]
private_subnets = [private_subnet_az1.id, private_subnet_az2.id]
public_sg_id = public_sg.id
private_sg_id = private_sg.id

# Export individual outputs using pulumi.export
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnets", [public_subnet_az1.id, public_subnet_az2.id])
pulumi.export("private_subnets", [private_subnet_az1.id, private_subnet_az2.id])
pulumi.export("public_sg_id", public_sg.id)
pulumi.export("private_sg_id", private_sg.id)
pulumi.export("rds_endpoint_id", rds_endpoint.id)
pulumi.export("ecs_endpoint_id", ecs_endpoint.id)
pulumi.export("ecs_agent_endpoint_id", ecs_agent_endpoint.id)
pulumi.export("ecs_telemetry_endpoint_id", ecs_telemetry_endpoint.id)

