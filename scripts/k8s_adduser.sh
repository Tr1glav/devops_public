#!/bin/bash

# add-user-serviceaccount.sh
set -e

USERNAME=$1
NAMESPACE=${2:-default}

if [ -z "$USERNAME" ]; then
    echo "Usage: $0 <username> [namespace]"
    echo "Example: $0 john default"
    exit 1
fi

echo "Creating ServiceAccount user: $USERNAME in namespace: $NAMESPACE"

# Create ServiceAccount
kubectl create serviceaccount $USERNAME -n $NAMESPACE

# Create RoleBinding (modify as needed)
kubectl create rolebinding $USERNAME-admin \
    --clusterrole=admin \
    --serviceaccount=$NAMESPACE:$USERNAME \
    --namespace=$NAMESPACE

# Get token
SECRET_NAME=$(kubectl get serviceaccount $USERNAME -n $NAMESPACE -o jsonpath='{.secrets[0].name}')
TOKEN=$(kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath='{.data.token}' | base64 --decode)

# Create kubeconfig
kubectl config set-credentials $USERNAME --token=$TOKEN
kubectl config set-context $USERNAME-context --cluster=minikube --user=$USERNAME --namespace=$NAMESPACE

echo "ServiceAccount user $USERNAME created successfully!"
echo "Token: $TOKEN"
echo "To use: kubectl --context=$USERNAME-context get pods"