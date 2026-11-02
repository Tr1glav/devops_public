# vault

Устанавливает [HashiCorp Vault](https://www.vaultproject.io/) бинарником: системный пользователь, raft-хранилище (HA), init/unseal (5 ключей, порог 3), UI, systemd-сервис.

## Использование

```yaml
- hosts: vault
  become: true
  roles:
    - vault
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `vault_version` | `1.20.4` | Версия Vault |
| `vault_user` / `vault_group` | `vault` | Системный пользователь/группа |
| `vault_config_dir` / `vault_data_dir` | `/etc/vault.d` / `/opt/vault/data` | Конфиг и данные |
| `vault_api_addr` | `http://{{ ansible_host }}:8200` | API-адрес |
| `vault_cluster_addr` | `http://{{ ansible_host }}:8201` | Адрес кластера |
| `vault_ha_storage` | `raft` | HA-хранилище |
| `vault_ui` | `true` | Включить UI |
| `vault_keyshares` / `vault_keythreshold` | `5` / `3` | Шамир: всего ключей / порог |
| `vault_unseal_keys` | `[]` | Ключи unseal (для авто-unseal) |
| `vault_root_token` | `""` | Root-токен (из Vault/секретов) |
| `vault_tls_disabled` | `true` | Отключить TLS (за haproxy) |

## Примечания

- Паттерн роли: бинарник качается на контроллер (`get_url` → `delegate_to: localhost`), затем `copy` + `unarchive` на ноду.
- К8s-вариант — роль `vault_k8s`.
