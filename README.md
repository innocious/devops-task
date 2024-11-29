# **AWS Infrastructure as Code (IaC) Demo**

---

## **Overview**
This demo project demonstrates the deployment of a foundational AWS infrastructure using **Pulumi (Python)**, showcasing Infrastructure as Code (IaC) practices. The project emphasizes **cost optimization** and **security** while employing a monolithic approach that integrates multiple layers (network, compute, monitoring, and data) within separate Pulumi stacks for modular management.

The infrastructure leverages essential AWS services like **VPC**, **ECS Fargate**, **RDS**, and the **ELK stack (Elasticsearch, Logstash, Kibana)**, enabling centralized log management and application hosting. This project serves as a starting point for small-scale environments and adheres to modern DevOps best practices.

---

## **Key Features**

### **1. Infrastructure Layers**
- **Network Layer**:
  - A VPC spanning **two Availability Zones (AZs)**.
  - **Public and private subnets** for optimal segregation of resources.
  - An **Internet Gateway** for public resources and a **NAT Gateway** for internet access from private subnets.
  - **VPC Endpoints** to reduce data transfer costs and secure access to AWS services.
- **Compute Layer**:
  - ECS Fargate cluster hosting an NGINX application.
  - Accessible through an **Application Load Balancer (ALB)** configured with HTTPS.
- **Data Layer**:
  - RDS PostgreSQL instance with:
    - Automated backups.
    - Encryption at rest and in transit.
    - Parameter groups for database tuning.
- **Monitoring Layer**:
  - Deployed Elasticsearch, Logstash, and Kibana (ELK stack) in ECS Fargate for centralized log aggregation and analysis.
  - Accessible via the default ALB DNS.

### **2. Cost Optimization**
- **Efficient Resource Allocation**:
  - AWS Free Tier options used wherever possible (e.g., `db.t3.micro` for RDS).
  - Minimal resource sizing for ECS Fargate tasks.
- **Reduced NAT Gateway Costs**:
  - A single NAT Gateway services all private subnets instead of deploying one per AZ.
- **Streamlined Subnet Design**:
  - Reduced the number of subnets to save IP address space and cost.

### **3. Security**
- **Network Isolation**:
  - Public-facing components (e.g., ALB) in public subnets, while critical resources (e.g., ECS tasks and RDS) reside in private subnets.
- **Granular Access Control**:
  - Security groups tightly scoped to allow only necessary communication.
  - IAM roles implement the **principle of least privilege**.
- **Encryption**:
  - RDS and ELK stack components use encryption at rest (KMS) and in transit (SSL/TLS).
- **Resource Tagging**:
  - Tags applied consistently for easy governance and cost tracking.

---

## **Limitations**
1. **Monolithic Design**:
   - This approach, while efficient for demos, may not scale well for larger projects.
   - In production, microservices-oriented deployments with separate repositories and CI/CD pipelines are recommended.
2. **Simplified Monitoring**:
   - The ELK stack setup lacks redundancy and advanced alerting mechanisms, which are critical for production environments.
3. **Single AZ Trade-offs**:
   - To optimize costs, some resources (e.g., NAT Gateway) are limited to a single AZ, introducing a potential **single point of failure**.

---

## **Setup Instructions**

### **Pre-requisites**
1. **Install Pulumi**
2. **Ensure the following are installed**
3. **AWS CLI v2: Install AWS CLI.**
4. **Python 3: Install Python.**



### **Configure AWS CLI:**
```bash
aws configure
```
Ensure valid AWS credentials are set up for the account where resources will be deployed.

Steps to Deploy
- Initialize Pulumi Backend State
- Run the `init.sh` script to create the S3 bucket for Pulumi’s backend state:
```bash
./init.sh
```

- Upload the setup.sh script for ELK stack provisioning to the S3 bucket:
```bash
./upload.sh
```

- Create AWS Key Pair
- Create an AWS key pair for EC2 instances:
```bash
aws ec2 create-key-pair --key-name my-ssh-key --query "KeyMaterial" --output text > my-ssh-key.pem
chmod 400 my-ssh-key.pem
```

## **Configure Pulumi**
Run the following commands to set the required configuration variables:
```bash
pulumi config set ami_id <your-ami-id>
pulumi config set instance_type t2.medium
pulumi config set db_username your-username
pulumi config set --secret db_password your-password
```
Install Dependencies
Install the Python dependencies from requirements.txt:
```bash
pip install -r requirements.txt
```
Preview Changes
Preview the infrastructure changes:
```bash
pulumi preview
```
Deploy the Infrastructure
Deploy the resources:
```bash
pulumi up
```
Follow the prompts to confirm the deployment.
Monitor Outputs
After deployment, note the outputs for:
Application URL: ALB DNS to access the NGINX application.
Kibana Dashboard URL: ALB DNS for Kibana.

## **Accessing Services**
NGINX Application: Access via the ALB DNS name provided in the outputs.
Kibana Dashboard: Access via /kibana path on the same ALB DNS.
