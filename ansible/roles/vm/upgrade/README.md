# vm/upgrade

Обновляет систему: `apt dist-upgrade` + autoremove/autoclean и установка базовых пакетов (gnupg2, software-properties-common, curl, python3, pip, venv, hvac).

## Использование

```yaml
- hosts: all
  become: true
  roles:
    - vm/upgrade
```

## Переменные

Нет.

## Примечания

- После обновления ядра появится `/var/run/reboot-required` — перезагрузит роль `vm/reboot`.
