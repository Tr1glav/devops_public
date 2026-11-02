# torrserver

Устанавливает [TorrServer](https://github.com/torrserver/torrserver) (торрент-сервер) в `/opt/torrserver`: системный пользователь, данные в `/opt/ts`, systemd-сервис, веб-интерфейс на порту 8090.

## Использование

```yaml
- hosts: torrserver
  become: true
  roles:
    - torrserver
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `torrserver_install_dir` | `/opt/torrserver` | Каталог установки |
| `torrserver_data_dir` | `/opt/ts` | Каталог данных |
| `torrserver_download_dir` | `/opt/ts/torrents` | Куда качать |
| `torrserver_port` | `8090` | Порт веб-интерфейса |
| `torrserver_ip` | `""` | Привязка к IP (пусто — все) |
| `torrserver_user` / `torrserver_group` | `torrserver` | Системный пользователь/группа |
| `torrserver_httpauth` | `false` | HTTP-аутентификация веб-интерфейса |
| `torrserver_readonly` | `false` | Режим только для чтения |
| `torrserver_log_dir` | `/var/log/torrserver` | Каталог логов |

## Примечания

- Хендлер: `Restart torrserver`.
