# vm/firewall

Базовый iptables-firewall: разрешает SSH (22), HTTPS (443), DNS (53), ICMP, established/related и loopback; политика INPUT по умолчанию **DROP**. Правила сохраняются через iptables-persistent (Debian).

## Использование

```yaml
- hosts: all
  become: true
  roles:
    - vm/firewall
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `allow_icmp` | `true` | Разрешить ping |

## Примечания

- Для дополнительных портов используйте отдельный iptables-задачу (см. `k3s`, `bgp_announcer` — открывают свои порты с тем же подходом).
