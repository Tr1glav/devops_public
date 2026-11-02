#!/usr/bin/env python3
"""BGP: сборка include-файла BIRD из внешних списков префиксов.

Источники — URL'ы по одному в строке в файле --sources. Каждый источник
парсится как список CIDR (по одному на строку; '#' и '//' — комментарии,
строки, начинающиеся с '!', пропускаются).

Отбрасываются: IPv6, приватные/служебные/мультикаст/loopback/reserved,
префиксы шире --min-prefixlen и default. При превышении --max-prefixes
файл не перезаписывается (лучше потерять обновление, чем залить пир
мусором). BIRD перезагружается только при реальном изменении набора.
"""
import argparse
import ipaddress
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

FETCH_TIMEOUT = 45
USER_AGENT = "bgp-lists-update/1.0 (+ansible)"

HEADER = """# Сгенерировано bgp_lists_update.py {ts}
# Префиксов: {count}
# Источники:
{srcs}
# Правки вручную будут перезаписаны.
"""


def read_sources(path):
    urls = []
    with open(path) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                urls.append(line)
    return urls


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
        return resp.read().decode("utf-8", "replace")


def is_skippable(net):
    return (net.version != 4
            or net.prefixlen == 0
            or net.is_private
            or net.is_loopback
            or net.is_link_local
            or net.is_multicast
            or net.is_reserved
            or net.is_unspecified)


def parse_text(text, min_prefixlen):
    nets, bad = [], 0
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].split("//", 1)[0].strip()
        if not line or line.startswith(("!", ";", "-")):
            continue
        token = line.split()[0].strip(",;")
        try:
            net = ipaddress.ip_network(token, strict=False)
        except ValueError:
            bad += 1
            continue
        if is_skippable(net) or net.prefixlen < min_prefixlen:
            continue
        nets.append(net)
    return nets, bad


def bird_line(net):
    return f"route {net.with_prefixlen} blackhole;\n"


def write_atomic(path, text):
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".announced.")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sources", default="/etc/bgp-announcer/sources.list")
    ap.add_argument("--output", default="/etc/bird/announced.conf")
    ap.add_argument("--birdc", default="/usr/sbin/birdc")
    ap.add_argument("--guard-state", default="/var/lib/bgp-announcer/guard.state",
                    help="файл состояния guard; если анонсы сняты — не поднимать")
    ap.add_argument("--min-prefixlen", type=int, default=8)
    ap.add_argument("--max-prefixes", type=int, default=50000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    urls = read_sources(args.sources)
    if not urls:
        print(f"[!] нет источников в {args.sources}", file=sys.stderr)
        return 1

    nets, failed = set(), []
    for url in urls:
        try:
            text = fetch(url)
        except (urllib.error.URLError, OSError) as e:
            failed.append(f"{url}: {e}")
            print(f"[!] {url}: {e}", file=sys.stderr)
            continue
        parsed, bad = parse_text(text, args.min_prefixlen)
        nets.update(parsed)
        print(f"[+] {url}: {len(parsed)} префиксов, пропущено строк {bad}")

    if not nets:
        print("[!] не удалось получить ни одного префикса, файл не трогаю",
              file=sys.stderr)
        return 1

    ordered = sorted(nets, key=lambda n: (int(n.network_address), n.prefixlen))
    if len(ordered) > args.max_prefixes:
        print(f"[!] префиксов {len(ordered)} > лимита {args.max_prefixes}, "
              f"файл не трогаю", file=sys.stderr)
        return 1

    srcs = "\n".join(f"#   {u}" for u in urls)
    body = HEADER.format(ts=time.strftime("%Y-%m-%d %H:%M:%S"), count=len(ordered),
                         srcs=srcs)
    body += "".join(bird_line(n) for n in ordered)

    if args.dry_run:
        print(body[:800])
        print(f"[dry-run] префиксов: {len(ordered)}")
        return 0

    old = ""
    if os.path.exists(args.output):
        with open(args.output) as f:
            old = f.read()
    def stripped(text):
        return "\n".join(line for line in text.splitlines()
                         if not line.startswith("# Сгенерировано"))

    if stripped(old) == stripped(body):
        print(f"[=] без изменений ({len(ordered)} префиксов), reload не нужен")
        return 0

    write_atomic(args.output, body)
    print(f"[*] записано {len(ordered)} префиксов в {args.output}")

    if not os.path.exists(args.birdc):
        print(f"[!] {args.birdc} не найден, BIRD не перезагружен", file=sys.stderr)
        return 1
    r = subprocess.run([args.birdc, "configure"], check=False,
                       capture_output=True, text=True, timeout=120)
    out = (r.stdout or "").strip()
    if r.returncode != 0:
        print(f"[!] birdc configure rc={r.returncode}: {out} "
              f"{(r.stderr or '').strip()}", file=sys.stderr)
        return 1
    print(f"[*] birdc configure: OK {out}")

    # birdc configure поднимает протоколы заново. Если guard снял анонсы
    # (туннель мёртв), возвращаем static_announced в выключенное состояние,
    # чтобы не анонсировать мёртвый туннель до следующего тика guard.
    try:
        with open(args.guard_state) as f:
            if json.load(f).get("withdrawn", False):
                subprocess.run([args.birdc, "disable", "static_announced"],
                               check=False, capture_output=True, text=True,
                               timeout=30)
                print("[*] guard снял анонсы — static_announced оставлен выключенным")
    except (OSError, ValueError):
        pass

    if failed:
        print(f"[!] часть источников недоступна: {failed}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
