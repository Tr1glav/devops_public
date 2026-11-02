# jackett

Устанавливает [Jackett](https://github.com/Jackett/Jackett) (индексатор торрентов) бинарником в `/opt/jackett`: системный пользователь, systemd-сервис, веб-интерфейс на порту 9117.

## Использование

```yaml
- hosts: jackett
  become: true
  roles:
    - jackett
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `jackett_install_dir` | `/opt/jackett` | Каталог установки |
| `jackett_port` | `9117` | Порт веб-интерфейса |
| `jackett_user` / `jackett_group` | `jackett` | Системный пользователь/группа |
| `jackett_service_name` | `jackett` | Имя systemd-сервиса |
| `jackett_arch` | `LinuxAMDx64` | Архитектура бинарника |
| `jackett_log_dir` | `/var/log/jackett` | Каталог логов |

## Примечания

- Хендлер: `Restart jackett`.
