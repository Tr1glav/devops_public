# Add Helm repository
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install Vault Operator
helm install vault-operator hashicorp/vault \
  --namespace vault-system \
  --create-namespace \
  --set global.enabled=false \
  --set server.enabled=false \
  --set injector.enabled=false \
  --set csi.enabled=false \
  --set operator.enabled=true