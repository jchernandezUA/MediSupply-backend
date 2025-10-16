#!/bin/bash

# Set your cluster name and region
CLUSTER_NAME="medisupply-cluster-1"
REGION="us-east-2"

# Delete EKS cluster (this also deletes nodegroups and related resources)
eksctl delete cluster --name $CLUSTER_NAME --region $REGION

# Delete CloudFormation stack (if any remains)
STACK_NAME="eksctl-$CLUSTER_NAME-cluster"
aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION

echo "Cluster, nodegroups, and CloudFormation stack deletion requested."