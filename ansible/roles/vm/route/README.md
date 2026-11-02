# vm/route

Устанавливает кастомный default gateway (`172.18.1.254`) на нат-VM: systemd-сервис `setup-routes` ждёт готовности сети и подменяет default-маршрут.

## Использование

```yaml
- hosts: nat-vms
  become: true
  roles:
    - vm/route
```

## Переменные

Нет (IP роутера зашит в задаче: `172.18.1.254`).

## Примечания

- Применяется к группе `nat-vms` (см. `playbooks/dla-prod/all.yml`).
