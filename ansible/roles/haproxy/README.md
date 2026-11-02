# haproxy

Устанавливает и настраивает HAProxy: конфиг из шаблона, **keepalived** для VIP (актив/пассив), SSL-сертификаты из Vault (`certs`), секреты из Vault (`infra`).

## Использование

```yaml
- hosts: haproxy
  become: true
  roles:
    - haproxy
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `haproxy_config` | `/etc/haproxy/haproxy.cfg` | Путь к конфигу |
| `haproxy_ssl_dir` | `/etc/haproxy/certs` | Каталог сертификатов |
| `haproxy_vault_mount` / `haproxy_vault_path` | `infra` / `{{ env }}/haproxy` | Секреты в Vault |

## Переменные окружения (group_vars)

| Переменная | Описание |
|---|---|
| `haproxy_vip_address` | VIP для keepalived (например `172.18.1.10/24`) |
| `haproxy_vip_interface` | Интерфейс для VIP (например `enp3s0`) |
| `haproxy_backends` | Список бэкендов |
| `haproxy_ssl_domains` | Домены, для которых выпускаются сертификаты (роль `certbot`) |

## Примечания

- Сертификаты — из Vault mounts `certs` (`{{ env }}/<домен>`).
- keepalived поднимает VIP между двумя нодами haproxy.
