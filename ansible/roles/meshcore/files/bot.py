import asyncio
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from typing import Callable
from meshcore import MeshCore, EventType

LOG_PATH = "/var/log/meshcore_bot.log"
CONNECTIONS_CHANNEL_NAME = "#connections"
chan_names: dict[int, str] = {}
connections_channel: int | None = None


def _ch_label(ch: int) -> str:
    return chan_names.get(ch, f"Канал {ch}")


def _setup_logging(debug: bool = False):
    log_dir = os.path.dirname(LOG_PATH)
    os.makedirs(log_dir, mode=0o755, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = RotatingFileHandler(LOG_PATH, maxBytes=10_000_000, backupCount=5)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.addHandler(ch)

    return logging.getLogger(__name__)


@dataclass
class Command:
    name: str
    handler: Callable
    admin_only: bool = False


_registry: list[Command] = []


def register(name: str, admin_only: bool = False):
    def wrapper(func):
        _registry.append(Command(name=name, handler=func, admin_only=admin_only))
        return func
    return wrapper


# ── commands ──────────────────────────────────────────────────────────


@register("ping")
async def _cmd_ping(meshcore: MeshCore, channel: int, text: str, data: dict):
    if channel != connections_channel:
        await meshcore.commands.send_chan_msg(channel, "ping доступен только в канале #connections")
        return
    path_len = data.get('path_len')
    path_hash_mode = data.get('path_hash_mode')
    if path_len in (0, 255) or path_hash_mode == -1:
        hop_str = "direct"
    else:
        hop_str = f"{path_len}"
    if hop_str == "direct":
        reply = f"hops:{hop_str}"
    else:
        path_hex = data.get('path')
        if path_hex is not None and path_hash_mode is not None and path_hash_mode >= 0:
            hash_size = path_hash_mode + 1
            nodes = []
            for i in range(0, len(path_hex), hash_size * 2):
                node = path_hex[i:i + hash_size * 2]
                nodes.append(node)
            route = " → ".join(nodes)
            reply = f"hops:{hop_str}, route:{route}"
        elif path_hex is not None:
            reply = f"hops:{hop_str}, path:{path_hex}"
        else:
            reply = f"hops:{hop_str}"
    logger = logging.getLogger(__name__)
    logger.info("[%s] /ping -> %s", _ch_label(channel), reply)
    await meshcore.commands.send_chan_msg(channel, reply)


async def _hass_request(url: str) -> str:
    if not url:
        return "HASS not configured"
    token = os.environ.get("HASS_TOKEN", "").strip()
    timeout = int(os.environ.get("HASS_TIMEOUT", "30"))

    logger = logging.getLogger(__name__)
    logger.info("HASS POST %s", url)

    req = urllib.request.Request(url, data=b"", method="POST")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(
            None, lambda: urllib.request.urlopen(req, timeout=timeout)
        )
        body = resp.read().decode()
        logger.info("HASS response: %d %s", resp.status, body[:200])
        return f"HASS: {resp.status} {body[:200]}"
    except urllib.error.HTTPError as e:
        logger.exception("HASS HTTP error")
        return f"HASS HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        logger.exception("HASS URL error")
        return f"HASS error: {e.reason}"
    except Exception as e:
        logger.exception("HASS error")
        return f"HASS error: {e}"


@register("gate", admin_only=True)
async def _cmd_gate(meshcore: MeshCore, channel: int, text: str, data: dict):
    logger = logging.getLogger(__name__)
    url = os.environ.get("HASS_GATE_URL", "").strip()
    logger.info("[%s] /gate trigger", _ch_label(channel))
    result = await _hass_request(url)
    logger.info("[%s] /gate result: %s", _ch_label(channel), result)
    await meshcore.commands.send_chan_msg(channel, f"GATE - {result}")


async def _ping_host(host: str, port: int = 443) -> str:
    try:
        t0 = asyncio.get_running_loop().time()
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=5
        )
        elapsed = asyncio.get_running_loop().time() - t0
        writer.close()
        await writer.wait_closed()
        return f"{host}: {elapsed*1000:.0f}"
    except asyncio.TimeoutError:
        return f"{host}: timeout"
    except Exception:
        return f"{host}: error"


@register("inet", admin_only=True)
async def _cmd_inet(meshcore: MeshCore, channel: int, text: str, data: dict):
    logger = logging.getLogger(__name__)
    logger.info("[%s] /inet check", _ch_label(channel))
    results = await asyncio.gather(
        _ping_host("google.com"),
        _ping_host("yandex.ru"),
    )
    reply = "\n".join(results)
    logger.info("[%s] /inet -> %s", _ch_label(channel), reply)
    await meshcore.commands.send_chan_msg(channel, reply)


async def _handle_messages(meshcore: MeshCore,
                           channel_index: int | None = None,
                           max_channels: int = 8,
                           auto_reconnect: bool = False):
    global connections_channel
    logger = logging.getLogger(__name__)

    def _on_channel_message(event):
        data = event.payload
        ch = data.get('channel_idx', 0)
        text = data.get('text', '')
        sender = data.get('pubkey_prefix', '?')[:8]
        msg = text
        if ": " in msg:
            name_part, msg = msg.split(": ", 1)
            sender = name_part.strip() or sender
        logger.info("[%s] от %s: %s", _ch_label(ch), sender, msg)

        stripped = msg.strip()
        for cmd in _registry:
            if not stripped.endswith(f'/{cmd.name}'):
                continue
            if cmd.admin_only and (channel_index is None or ch != channel_index):
                return
            asyncio.create_task(cmd.handler(meshcore, ch, msg, data))
            break

    if auto_reconnect:
        async def _on_connected(event):
            logger.info("Подключено: %s", event.payload)
            if event.payload.get('reconnected'):
                logger.info("Успешно переподключились!")
                await meshcore.start_auto_message_fetching()

        async def _on_disconnected(event):
            reason = event.payload.get('reason', 'Unknown')
            logger.info("Отключено: %s", reason)
            if event.payload.get('max_attempts_exceeded'):
                logger.warning("Достигнуто макс. число попыток переподключения")

        meshcore.subscribe(EventType.CONNECTED, _on_connected)
        meshcore.subscribe(EventType.DISCONNECTED, _on_disconnected)

    sub = meshcore.subscribe(EventType.CHANNEL_MSG_RECV, _on_channel_message)

    logger.info("Проверка доступных каналов...")
    for i in range(max_channels):
        result = await meshcore.commands.get_channel(i)
        if result.type == EventType.ERROR:
            continue
        name = result.payload.get('channel_name', '')
        if name:
            chan_names[i] = f"Канал {i} ({name})"
            logger.info("  %s", chan_names[i])
            if name.strip() == CONNECTIONS_CHANNEL_NAME:
                connections_channel = i
    if connections_channel is None:
        for i in range(max_channels):
            if i not in chan_names:
                result = await meshcore.commands.set_channel(i, CONNECTIONS_CHANNEL_NAME)
                if result.type == EventType.ERROR:
                    logger.warning("Не удалось создать %s: %s", CONNECTIONS_CHANNEL_NAME, result.payload)
                else:
                    connections_channel = i
                    chan_names[i] = f"Канал {i} ({CONNECTIONS_CHANNEL_NAME})"
                    logger.info("Создан %s (канал %d)", CONNECTIONS_CHANNEL_NAME, i)
                    break
    if connections_channel is not None:
        logger.info("Канал подключений: %s", _ch_label(connections_channel))
    elif channel_index is not None:
        logger.info("Управляющий канал: %s", _ch_label(channel_index))

    meshcore.set_decrypt_channel_logs(True)

    advert_task = None
    advert_flood_task = None

    logger.info("Прослушивание начато. Нажмите Ctrl+C для выхода")
    await meshcore.start_auto_message_fetching()

    async def _advert_loop():
        while True:
            await asyncio.sleep(3600)
            try:
                await meshcore.commands.send_advert(flood=False)
                logger.info("Advert sent (direct)")
            except Exception as e:
                logger.warning("Advert error: %s", e)

    async def _advert_flood_loop():
        while True:
            await asyncio.sleep(7200)
            try:
                await meshcore.commands.send_advert(flood=True)
                logger.info("Advert sent (flood)")
            except Exception as e:
                logger.warning("Advert flood error: %s", e)

    advert_task = asyncio.create_task(_advert_loop())
    advert_flood_task = asyncio.create_task(_advert_flood_loop())

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        if advert_task:
            advert_task.cancel()
        if advert_flood_task:
            advert_flood_task.cancel()
        await meshcore.stop_auto_message_fetching()
        meshcore.unsubscribe(sub)
        await meshcore.disconnect()
        logger.info("Отключено")


async def listen(host: str, port: int, channel_index: int | None = None,
                 max_channels: int = 8, auto_reconnect: bool = False):
    logger = logging.getLogger(__name__)
    logger.info("Подключение к %s:%d...%s",
                host, port,
                " (авто-переподключение)" if auto_reconnect else "")
    meshcore = await MeshCore.create_tcp(
        host, port, debug=False,
        auto_reconnect=auto_reconnect,
        max_reconnect_attempts=10 if auto_reconnect else 0,
    )
    logger.info("Подключено успешно!")
    await _handle_messages(meshcore, channel_index, max_channels, auto_reconnect)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="MeshCore бот для прослушивания сообщений в каналах"
    )
    parser.add_argument("--host", default="192.168.0.50",
                        help="IP-адрес устройства (по умолчанию: 192.168.0.50)")
    parser.add_argument("--port", type=int, default=5000,
                        help="TCP-порт (по умолчанию: 5000)")
    parser.add_argument("-c", "--channel", type=int, default=None,
                        help="Номер канала (по умолчанию: все каналы)")
    parser.add_argument("--max-channels", type=int, default=8,
                        help="Макс. количество каналов для проверки (по умолчанию: 8)")
    parser.add_argument("--auto-reconnect", action="store_true",
                        help="Авто-переподключение при потере связи")
    parser.add_argument("--debug", action="store_true",
                        help="Режим отладки (debug-логи)")

    args = parser.parse_args()
    logger = _setup_logging(debug=args.debug)

    try:
        asyncio.run(listen(args.host, args.port, args.channel,
                           args.max_channels, args.auto_reconnect))
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except ConnectionRefusedError:
        logger.error("Не удалось подключиться к %s:%d", args.host, args.port)
        logger.error("Проверьте, что устройство доступно и порт правильный")
        raise SystemExit(1)
    except Exception as e:
        logger.error("Ошибка: %s", e)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
