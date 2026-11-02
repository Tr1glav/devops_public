# vm

Группа небольших ролей для базовой настройки VM/контейнеров. Используются плейбуками окружений (например, `dla-prod/all.yml`).

| Роль | Назначение |
|---|---|
| [`check_container`](check_container/) | Определение, является ли хост контейнером (LXC/Docker/LXD); факты `vm_is_container`, `vm_is_lxc` |
| [`firewall`](firewall/) | Базовый iptables-firewall: SSH/HTTPS/DNS/ICMP, default DROP, iptables-persistent |
| [`install_qemu_guest`](install_qemu_guest/) | qemu-guest-agent на не-контейнерах |
| [`logrotate`](logrotate/) | Базовые logrotate-конфиги |
| [`node_exporter`](node_exporter/) | node_exporter для Prometheus |
| [`reboot`](reboot/) | Перезагрузка по флагу `/var/run/reboot-required` (на k8s-нодах — с drain) |
| [`resolved`](resolved/) | systemd-resolved: DNS = группа `dnsmasq`, fallback 8.8.8.8 |
| [`route`](route/) | Кастомный default gateway (172.18.1.254) через systemd-сервис |
| [`router`](router/) | NAT/SNAT для локальной подсети (Cloud.ru) |
| [`upgrade`](upgrade/) | apt dist-upgrade + базовые пакеты |

## Использование

```yaml
- hosts: all
  become: true
  roles:
    - vm/resolved
    - vm/logrotate

- hosts: nat-vms
  become: true
  roles:
    - vm/route
```

## Примечания

- `check_container` нужно применять **до** остальных ролей (ставит факты, которыми они пользуются).
- Роли без `defaults/` не имеют настраиваемых переменных.
