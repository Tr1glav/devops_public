# awx_k8s

Разворачивает [AWX](https://awx.readthedocs.io/) в k3s-кластере через официальный [awx-operator](https://github.com/ansible/awx-operator) (Helm): ставит Helm, добавляет репозиторий, деплоит оператора и CR AWX.

По умолчанию AWX публикуется через **NodePort** (traefik в роли `k3s` отключён) и заводится бэкендом в haproxy. БД — managed (поднимает оператор) или unmanaged (внешняя, роль `postgres`).

## Использование

```yaml
- hosts: k3s-server
  become: true
  roles:
    - awx_k8s
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `awx_k8s_operator_version` | `2.19.1` | Версия awx-operator |
| `awx_k8s_namespace` | `awx` | Namespace |
| `awx_k8s_domain` | `awx.{{ domain }}` | Домен для сертификата |
| `awx_k8s_kubeconfig` | `/etc/rancher/k3s/k3s.yaml` | Kubeconfig |
| `awx_k8s_service_type` / `awx_k8s_nodeport_port` | `NodePort` / `30080` | Публикация сервиса |
| `awx_k8s_postgres_type` | `managed` | `managed` — postgres оператора, `unmanaged` — внешний |
| `awx_k8s_db_name` / `awx_k8s_db_user` | `awx` | Параметры внешней БД |
| `awx_k8s_db_host` / `awx_k8s_db_port` / `awx_k8s_db_password` | `localhost` / `5432` / `""` | Адрес внешней БД (пароль из Vault) |
| `awx_k8s_postgres_storage_size` | `20Gi` | Размер БД-тома (managed) |
| `awx_k8s_storage_class` | `""` | StorageClass (default — local) |
| `awx_k8s_projects_persistence` | `true` | Персистентность проектов |
| `awx_k8s_web_replicas` / `awx_k8s_task_replicas` | `1` | Реплики web/task |
| `awx_k8s_web_resources` / `awx_k8s_task_resources` / `awx_k8s_ee_resources` | 1Gi/500m и т.д. | Лимиты ресурсов |
| `awx_k8s_vault_mount` / `awx_k8s_vault_path` | `infra` / `{{ env }}/awx` | Секреты в Vault |
| `awx_k8s_enable_ssl` | `false` | TLS на сертификате из `certs` |
| `awx_k8s_wait_timeout` | `900` | Таймаут ожидания готовности, сек |

## Примечания

- Секреты (пароль admin, пароль БД) — из Vault `infra/<env>/awx`.
- При `unmanaged` БД создаёт роль `postgres`.
