#!/bin/bash
set -e

kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/database.yaml
kubectl apply -f k8s/book-service.yaml
kubectl apply -f k8s/order-service.yaml
kubectl apply -f k8s/api-gateway.yaml
kubectl apply -f k8s/frontend.yaml

echo "Waiting for database..."
kubectl rollout status deployment/database --timeout=120s

./scripts/seed-data.sh

