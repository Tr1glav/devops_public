# vm/install_qemu_guest

Устанавливает и запускает `qemu-guest-agent` на физических VM (на контейнерах пропускается).

## Использование

```yaml
- hosts: all
  become: true
  roles:
    - vm/check_container
    - vm/install_qemu_guest
```

## Переменные

Нет.

## Примечания

- Установка пакета выполняется только в окружении `dev` (`env == 'dev'`); сервис стартует на всех не-контейнерах.
- Требует факты роли `vm/check_container`.
