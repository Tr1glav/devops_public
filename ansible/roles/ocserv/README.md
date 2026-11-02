# ocserv

Разворачивает [ocserv](https://ocserv.natechoff.com/) VPN-сервер на роутере: пользователи из Vault, сертификат из Vault (`certs`), `ocpasswd`, iptables.

## Использование

```yaml
- hosts: router
  become: true
  roles:
    - ocserv
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `ocserv_hostname` | `vpn.{{ domain }}` | Домен сервера |
| `ocserv_port` / `ocserv_proto` | `443` / `tcp` | Порт и протокол |
| `ocserv_ip_range` / `ocserv_netmask` | `172.17.21.0/24` / `255.255.255.0` | Подсеть VPN |
| `ocserv_auth_method` | `plain[passwd=/etc/ocserv/ocpasswd]` | Метод аутентификации |
| `ocserv_vault_mount` / `ocserv_vault_path` | `infra` / `prod/vpn/users` | Пользователи VPN в Vault |
| `ocserv_certs_vault_mount` / `ocserv_certs_vault_path` | `certs` / `{{ env }}/{{ ocserv_hostname }}` | Сертификат в Vault |
| `ocserv_use_self_signed` | `false` | Самозавершённый сертификат |
| `ocserv_cert_path` / `ocserv_key_path` / `ocserv_ca_path` | `/etc/ocserv/*.pem` | Пути к сертификатам |

## Примечания

- Клиентская сторона — роль `openconnect_client`.
- Хендлер: `Restart ocserv`.
