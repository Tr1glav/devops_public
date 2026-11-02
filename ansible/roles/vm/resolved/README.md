# vm/resolved

Настраивает systemd-resolved: основной DNS — хосты из группы `dnsmasq`, fallback — 8.8.8.8/77.88.8.8. Симлинк `/etc/resolv.conf` на stub.

## Использование

```yaml
- hosts: all
  become: true
  roles:
    - vm/resolved
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `resolved_conf_dns` | `{{ groups['dnsmasq'] }}` | DNS-серверы (группа инвентаря) |
| `resolved_conf_fallback_dns` | `8.8.8.8, 77.88.8.8` | Fallback DNS |

## Примечания

- В инвентаре должна быть группа `dnsmasq`.
- Хендлер: `Restart systemd-resolved`.
