# vm/check_container

Определяет, является ли хост контейнером (LXC/Docker/LXD), по `/proc/1/environ`, `/.dockerenv`, `/dev/lxd/sock`. Ставит факты:

- `vm_is_container` — true, если хост контейнер;
- `vm_is_lxc` — true, если именно LXC.

## Использование

```yaml
- hosts: all
  roles:
    - vm/check_container
```

## Переменные

Нет.

## Примечания

- Применяйте **до** ролей, которые зависят от фактов (`vm/reboot`, `vm/install_qemu_guest`).
- Роль не меняет систему (`changed_when: false`).
