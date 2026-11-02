# vm/router

Настраивает роутер (Cloud.ru): включает IP-forwarding, настраивает SNAT для локальной подсети (WAN-интерфейс определяется автоматически).

## Использование

```yaml
- hosts: router
  become: true
  roles:
    - vm/router
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `router_wan_interface` | `{{ ansible_default_ipv4.interface }}` | WAN-интерфейс |
| `router_lan_interface` | `{{ ansible_default_ipv4.interface }}` | LAN-интерфейс |
| `router_local_subnet` | `192.168.0.0/24` | Локальная подсеть для SNAT |
| `router_internal_ip` | `{{ ansible_default_ipv4.address }}` | Внутренний IP роутера |

## Примечания

- Перед добавлением SNAT существующие правила POSTROUTING очищаются (защита от конфликтов).
