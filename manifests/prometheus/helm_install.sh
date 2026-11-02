# Добавляем репозиторий Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Устанавливаем Prometheus Stack (включает Grafana)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin