# cloudflare

Управляет DNS-зонами Cloudflare: берёт API-токен из Vault, ставит коллекцию `community.cloudflare` и обновляет DNS-записи доменов.

## Использование

```yaml
- hosts: localhost
  become: false
  roles:
    - cloudflare
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `cloudflare_vault_secret_path` | `external/data/dns/cloudflare` | Путь токена в Vault |
| `cloudflare_vault_validate_certs` | `true` | Проверять TLS-сертификат Vault |

## Примечания

- Работает на контроллере (без become).
- Список доменов для записей — в group_vars.
