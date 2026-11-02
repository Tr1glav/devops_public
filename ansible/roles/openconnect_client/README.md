# openconnect_client

Настраивает [OpenConnect](https://www.infradead.org/openconnect/) клиент для VPN на ocserv: фоновое подключение, интерфейс `vpn0`, маршруты (внутренняя сеть через VPN, остальной трафик — напрямую), MTU 1400. Креды пользователя — из Vault.

## Использование

```yaml
- hosts: vpn-clients
  become: true
  roles:
    - openconnect_client
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `openconnect_client_server` | `vpn.dla.su` | Адрес VPN-сервера |
| `openconnect_client_port` | `443` | Порт сервера |
| `openconnect_client_vpn_network` | `172.17.21.0/24` | Подсеть VPN (маршрут через туннель) |
| `openconnect_client_interface` | `vpn0` | Имя интерфейса |
| `openconnect_client_mtu` | `1400` | MTU |
| `openconnect_client_reconnect_timeout` | `30` | Таймаут переподключения |
| `openconnect_client_background` | `true` | Фоновый режим |
| `openconnect_client_background_script` | `true` | Использовать background-скрипт (systemd) |
| `openconnect_client_use_certificate` | `false` | Аутентификация по сертификату |
| `openconnect_client_server_cert_hash` | `""` | Проверка сертификата сервера по hash |
| `openconnect_client_vault_mount` / `openconnect_client_vault_path` | `infra` / `prod/vpn/users` | Креды в Vault |

## Примечания

- Маршрут в локальную сеть хоста (`ansible_default_ipv4`) не идёт через VPN.
- Хендлеры: `Restart openconnect`, `Reload systemd`.
