# vm/reboot

Перезагружает хост, если существует файл `/var/run/reboot-required` (ставится apt после обновления ядра и т.п.). Контейнеры пропускаются. На k8s-нодах перед перезагрузкой — `kubectl drain`, после — `uncordon`.

## Использование

```yaml
- hosts: all
  become: true
  roles:
    - vm/check_container
    - vm/reboot
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `reboot_required_file` | `/var/run/reboot-required` | Флаг необходимости перезагрузки |
| `security_only` | `false` | Перезагружать только при обновлениях безопасности |

## Примечания

- Требует факты роли `vm/check_container` (`vm_is_container`) и факт `is_k8s_node` (для k8s-ветки).
- Роль завершает play после старта перезагрузки.
