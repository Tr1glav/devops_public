# cache_server

Nginx-кэш для GitHub: два контура —

- **api/raw** (порт 80): прокси `api.github.com` и `raw.githubusercontent.com` с кэшем;
- **ghrc** (порт 8080, домен `github-cache.<env>.<domain>`): кэш GitHub Releases — бинарники качаются через него (см. `prometheus_url`, `etcd_url`, `node_exporter_url`).

Включены stale-while-revalidate, background update, lock, опциональный rate limit, SSL.

## Использование

```yaml
- hosts: cache-server
  become: true
  roles:
    - cache_server
```

## Переменные (основные)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `nginx_github_cache_port` | `80` | Порт api/raw-кэша |
| `nginx_github_cache_path` | `/var/cache/nginx/github` | Каталог кэша |
| `nginx_github_cache_max_size` | `50g` | Максимальный размер кэша |
| `nginx_github_cache_valid_time` | `10m` | Время жизни записи |
| `nginx_github_api_upstream` / `nginx_github_raw_upstream` | api/raw GitHub | Апстримы |
| `nginx_ghrc_cache_port` | `8080` | Порт releases-кэша |
| `nginx_ghrc_cache_server_name` | `github-cache.{{ product_env }}.{{ domain }}` | Домен ghrc |
| `nginx_ghrc_cache_max_size` / `nginx_ghrc_releases_cache_max_size` | `50g` / `100g` | Размеры кэшей |
| `nginx_ghrc_cache_valid_time` | `24h` | Время жизни записи releases |
| `nginx_ghrc_rate_limit_enabled` | `false` | Rate limit (10r/s, burst 20) |
| `nginx_ghrc_cache_ssl_cert` / `nginx_ghrc_cache_ssl_key` | `/etc/ssl/certs/ghrc-cache.*` | Сертификат (из Vault `certs`) |
| `nginx_worker_processes` / `nginx_worker_connections` | `auto` / `1024` | Работники nginx |

Полный список (таймауты, буферы, stale-правила) — в `defaults/main.yml`.

## Примечания

- Сертификаты — из Vault mounts `certs` (`{{ env }}/{{ nginx_ghrc_cache_server_name }}`).
- Домены для выпуска сертификатов — в `cache_servers` (group_vars), выпускает роль `certbot`.
