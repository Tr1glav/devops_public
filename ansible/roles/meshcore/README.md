# meshcore

Разворачивает meshcore-бота (Python): venv, `bot.py` (или пакет `meshcore` из pip), logrotate, systemd-сервис. Секреты (токен Home Assistant) — из Vault.

## Использование

```yaml
- hosts: meshcore
  become: true
  roles:
    - meshcore
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `meshcore_service_name` | `meshcore` | Имя systemd-сервиса |
| `meshcore_user` / `meshcore_group` | `meshcore` | Системный пользователь/группа |
| `meshcore_home` | `/opt/meshcore` | Каталог приложения (logs/, config/, venv/) |
| `meshcore_host` | `192.168.0.50` | Адрес meshcore-шлюза |
| `meshcore_port` | `5000` | Порт шлюза |
| `meshcore_channel` / `meshcore_max_channels` | `1` / `8` | Канал(ы) |
| `meshcore_auto_reconnect` | `true` | Автопереподключение |
| `meshcore_python_package` | `meshcore` | Пакет для установки в venv |
| `meshcore_venv_path` | `{{ meshcore_home }}/venv` | Путь к venv |
| `meshcore_hass_token` | `""` | Токен Home Assistant (из Vault) |
| `meshcore_hass_timeout` | `10` | Таймаут запросов к HA |
| `meshcore_debug` | `false` | Режим отладки |
| `meshcore_vault_mount` / `meshcore_vault_path` | `apps` / `home/homeassistans/webhooks` | Секреты в Vault |

## Переменные окружения (group_vars)

| Переменная | Описание |
|---|---|
| `meshcore_local_script` | `true` (по умолчанию) — деплоить локальный `bot.py` из роли; `false` — только pip-пакет |
| `meshcore_extra_packages` | Список дополнительных pip-пакетов |

## Примечания

- Хендлер: `Restart meshcore`.
