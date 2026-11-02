# certbot

Выпускает и продлевает Let's Encrypt сертификаты через **Cloudflare DNS-01 challenge** для доменов haproxy (`haproxy_ssl_domains`) и cache-server'ов (`cache_servers`). Токен Cloudflare берётся из Vault.

## Использование

```yaml
- hosts: localhost
  become: false
  gather_facts: false
  roles:
    - certbot
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `certbot_email` | `myumukhametzyanov@gmail.com` | Почта для Let's Encrypt |
| `certbot_expand_existing` | `true` | Добавлять домены в существующие сертификаты |
| `certbot_vault_cf_mount` | `external` | Mount Vault с токеном Cloudflare |
| `certbot_vault_cf_path` | `dns/cloudflare` | Путь в mount |

## Примечания

- Токен Cloudflare — из Vault `external/data/dns/cloudflare`.
- Требуется переменная `haproxy_ssl_domains` (group_vars) — список доменов haproxy.
- Выпуск делается на контроллере (`delegate_to: localhost`).
