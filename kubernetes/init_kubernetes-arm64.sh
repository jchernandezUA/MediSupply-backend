#!/bin/bash

# Login to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 012146976167.dkr.ecr.us-east-2.amazonaws.com

# Build and push images (arm64)
docker buildx build --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/auth-usuario:latest --push ./auth-usuario
docker buildx build --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/mediador-web:latest --push ./mediador-web
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/producto-inventario-web:latest --push ./producto-inventario-web
docker buildx build --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/productos:latest --push ./productos_microservice
docker buildx build --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/vendedores:latest --push ./vendedores_microservice
docker buildx build --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/proveedores:latest --push ./proveedores_microservice

# Create EKS cluster
eksctl create cluster --name medisupply-cluster-1 --region us-east-2 --nodes 9 --node-type t3.micro

# Configure kubectl
aws eks --region us-east-2 update-kubeconfig --name medisupply-cluster-1

# Deploy to Kubernetes
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/postgres-secret.yaml
kubectl apply -f kubernetes/postgres-deployment.yaml
kubectl apply -f kubernetes/postgres-service.yaml
kubectl apply -f kubernetes/auth-usuario/deployment.yaml
kubectl apply -f kubernetes/auth-usuario/service.yaml
kubectl apply -f kubernetes/mediador-web/deployment.yaml
kubectl apply -f kubernetes/mediador-web/service.yaml
kubectl apply -f kubernetes/producto-inventario-web/deployment.yaml
kubectl apply -f kubernetes/producto-inventario-web/service.yaml
kubectl apply -f kubernetes/productos/deployment.yaml
kubectl apply -f kubernetes/productos/service.yaml
kubectl apply -f kubernetes/proveedores/deployment.yaml
kubectl apply -f kubernetes/proveedores/service.yaml
kubectl apply -f kubernetes/vendedores/deployment.yaml
kubectl apply -f kubernetes/vendedores/service.yaml
kubectl apply -f kubernetes/ingress.yaml