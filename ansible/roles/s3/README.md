# s3

Монтирует S3-бакет (s3.cloud.ru) в файловую систему через [goofys](https://github.com/emc/goofys). Ключи доступа — из Vault.

## Использование

```yaml
- hosts: storage
  become: true
  roles:
    - s3
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `s3_endpoint` | `https://s3.cloud.ru` | Эндпоинт S3 |
| `s3_bucket` | `nextcloud` | Бакет для монтирования |
| `s3_region` | `ru-central-1` | Регион |
| `s3_mount_point` | `/mnt/s3-storage` | Точка монтирования |
| `s3_vault_mount` / `s3_vault_path` | `infra` / `{{ env }}/s3_secrets` | Ключи в Vault |

## Примечания

- Используется, например, как хранилище для Nextcloud (см. роль `nextcloud`).
