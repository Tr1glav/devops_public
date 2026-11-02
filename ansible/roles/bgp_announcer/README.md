# bgp_announcer

BGP-экспортёр списков блокировок: BIRD2 на `wh-list-1` анонсирует MikroTik'у префиксы из списков на GitHub (AntiZapret: google/discord/telegram + antifilter). Домашний трафик к этим префиксам приходит на этот хост и уходит в туннель (TPROXY, см. роль `tunnel_client`).

Health-guard: пока туннель мёртв (нет ответа через SOCKS Xray), протокол с анонсами гасится — MikroTik снимает маршруты и уходит к провайдеру. Сессия BGP при этом остаётся Established (сосед не видит flap).

## Использование

```yaml
- hosts: wh-list
  become: true
  roles:
    - bgp_announcer
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `bgp_announcer_enabled` | `true` | Включить роль |
| `bgp_announcer_local_as` | `64512` | Локальный private ASN (RFC 6996) |
| `bgp_announcer_peer_as` | `64999` | ASN пир (MikroTik) |
| `bgp_announcer_router_id` | `172.16.254.250` | Router ID хоста |
| `bgp_announcer_peer_address` | `172.16.0.1` | Адрес пир-роутера |
| `bgp_announcer_multihop` | `2` | TTL для eBGP через маршрутизатор |
| `bgp_announcer_sources` | google/discord/telegram + antifilter | URL списков префиксов |
| `bgp_announcer_min_prefixlen` | `8` | Не анонсировать префиксы шире |
| `bgp_announcer_max_prefixes` | `50000` | Лимит, при превышении файл не обновляется |
| `bgp_announcer_update_interval` | `1h` | Периодичность обновления списков |
| `bgp_announcer_firewall_enabled` | `true` | Открыть 179/tcp для сетей пира |
| `bgp_announcer_allowed_networks` | `172.16/16, 192.168/23` | Сети, которым разрешён BGP |
| `bgp_announcer_guard_enabled` | `true` | Включить health-guard |
| `bgp_announcer_guard_probe_url` | `https://www.gstatic.com/generate_204` | URL проверки туннеля |
| `bgp_announcer_guard_fail_threshold` / `bgp_announcer_guard_ok_threshold` | `3` / `5` | Пороги срабатывания/восстановления |
| `bgp_announcer_guard_interval` | `30s` | Периодичность проверки |
| `bgp_announcer_socks_port` | `10808` | SOCKS-порт Xray (см. `tunnel_client`) |
| `bgp_announcer_route_protocol` | `static_announced` | Протокол BIRD с анонсами (гасится guard'ом) |

## Примечания

- Работает в паре с `tunnel_client` (туннель) и `vm/firewall` (правила iptables).
- Пути: `/etc/bgp-announcer/`, `/etc/bird/announced.conf`, скрипты в `/usr/local/bin/bgp-*.py`.
