provider "aws" {
  region = "ap-south-1"
}

# ---- VPC ----
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  name = "eks-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["ap-south-1a", "ap-south-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.3.0/24", "10.0.4.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}

# ---- EKS CLUSTER ----
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.8.5"

  cluster_name    = "my-eks-cluster"
  cluster_version = "1.29"
  subnet_ids      = module.vpc.private_subnets
  vpc_id          = module.vpc.vpc_id

  cluster_endpoint_public_access = true

  tags = {
    Environment = "dev"
  }
}

# ---- NODE GROUP (separate) ----
resource "aws_eks_node_group" "default" {
  cluster_name    = module.eks.cluster_name
  node_group_name = "default-ng"
  node_role_arn   = module.eks.node_iam_role_arn
  subnet_ids      = module.vpc.private_subnets

  scaling_config {
    desired_size = var.desired_size
    max_size     = 5
    min_size     = 1
  }

  instance_types = ["t3.medium"]
  capacity_type  = "ON_DEMAND"

  tags = {
    Name = "default-ng"
  }
}
