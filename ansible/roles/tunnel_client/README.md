# tunnel_client

Поднимает туннель на [Xray-core](https://github.com/XTLS/Xray-core): локальные SOCKS (10808) и HTTP (10809) прокси + **TPROXY-транзит** — трафик с других хостов сети, идущий через этот хост, прозрачно уходит сквозь туннель. Креды — из Vault.

## Использование

```yaml
- hosts: wh-list
  become: true
  roles:
    - tunnel_client
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `tunnel_client_xray_version` | `26.10.21` | Версия Xray-core |
| `tunnel_client_install_dir` | `/opt/tunnel-client` | Каталог установки |
| `tunnel_client_socks_port` / `tunnel_client_http_port` | `10808` / `10809` | Локальные прокси-порты |
| `tunnel_client_tproxy_enabled` | `true` | Включить TPROXY-транзит |
| `tunnel_client_tproxy_port` | `10810` | Порт dokodemo-door inbound |
| `tunnel_client_transit_sources` | `172.16/16, 192.168/23` | Сети-источники транзитного трафика |
| `tunnel_client_tproxy_bypass_ports` | `22, 179` | Порты, НЕ уходящие в туннель (SSH — доступность управления, BGP — петля) |
| `tunnel_client_creds_file` | `/etc/tunnel-client/creds` | Файл кредов (LOGIN=/PASSWORD=) |
| `tunnel_client_login` / `tunnel_client_password` | `""` | Фолбэк-креды, если их нет в Vault |
| `tunnel_client_use_vault` | `true` | Брать креды из Vault |
| `tunnel_client_vault_mount` / `tunnel_client_vault_path` | `infra` / `dev/wh-list` | Креды в Vault |
| `tunnel_client_bootstrap_dns` | `9.9.9.9, 149.112.112.112` | Резолверы для бустрапа (1.1.1.1/8.8.8.8 завёрнуты в туннель) |
| `tunnel_client_service_cmd` | `best --proxy` | Команда запуска (fetch + check + run) |

## Примечания

- Работает в паре с `bgp_announcer`: guard проверяет туннель через SOCKS `tunnel_client_socks_port`.
- systemd-сервис `tunnel-client`, режим `best --proxy` — самовосстановление при старте.
