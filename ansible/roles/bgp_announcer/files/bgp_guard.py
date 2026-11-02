#!/usr/bin/env python3
"""Health-guard: снимает анонсы, когда туннель не работает.

Идея: MikroTik получает маршруты только пока жив туннель. Туннель умер ->
адреса перестают отдаваться -> домашний трафик уходит к провайдеру напрямую.
Как только туннель ожил — анонсы возвращаются.

BGP-сессия при этом НЕ трогается: guard выключает протокол static_announced,
из которого BIRD экспортирует префиксы. Сессия остаётся Established, уходят
только маршруты — соседи не видят flap и не перестраивают сессию.

Проверка идёт через SOCKS-порт Xray (он же путь реального трафика), а не
пингом интерфейса.

Гистерезис: --fail-threshold подряд неудач -> снять анонсы, --ok-threshold
подряд успехов -> вернуть. Состояние хранится в --state.

Желаемое состояние на каждом прогоне приводится к факту (birdc show
protocols): если BIRD перезапустился или анонсы включились через
birdc configure, guard вернёт их в нужное положение на ближайшем тике.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile


def probe(port, url, expect, timeout):
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
           "--socks5-hostname", f"127.0.0.1:{port}",
           "--max-time", str(timeout), url]
    try:
        r = subprocess.run(cmd, check=False, capture_output=True,
                           text=True, timeout=timeout + 5)
    except (subprocess.SubprocessError, OSError):
        return False
    return (r.stdout or "").strip() == str(expect)


def birdc(command, timeout=30):
    try:
        r = subprocess.run(["birdc", command], check=False, capture_output=True,
                           text=True, timeout=timeout)
    except (subprocess.SubprocessError, OSError) as e:
        print(f"[!] birdc {command}: {e}", file=sys.stderr)
        return False
    if r.returncode != 0:
        print(f"[!] birdc {command}: {(r.stderr or r.stdout).strip()}",
              file=sys.stderr)
        return False
    return True


def bird_proto_state(protocol):
    """Строка состояния протокола в BIRD (например down/up/start) или None.

    Вывод birdc: "BIRD 2.14 ready.", шапка, затем строка протокола
    "<name> <proto> <table> <state> <since> <info>".
    """
    try:
        r = subprocess.run(["birdc", "show", "protocols", protocol], check=False,
                           capture_output=True, text=True, timeout=30)
    except (subprocess.SubprocessError, OSError):
        return None
    if r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) > 3 and parts[0] == protocol:
            return parts[3]
    return None


def load_state(path):
    try:
        with open(path) as f:
            st = json.load(f)
        # disabled — ключ прошлой версии (гасили BGP-сессию), читаем для миграции
        return {"fails": int(st.get("fails", 0)),
                "oks": int(st.get("oks", 0)),
                "withdrawn": bool(st.get("withdrawn",
                                         st.get("disabled", False)))}
    except (OSError, ValueError):
        return {"fails": 0, "oks": 0, "withdrawn": False}


def save_state(path, st):
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".guard.")
    with os.fdopen(fd, "w") as f:
        json.dump(st, f)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--socks-port", type=int, default=10808)
    ap.add_argument("--url", default="https://www.gstatic.com/generate_204")
    ap.add_argument("--expect", type=int, default=204)
    ap.add_argument("--protocol", default="static_announced",
                    help="протокол с анонсами, который гасим (не BGP-сессия)")
    ap.add_argument("--bgp-protocol", default="mikrotik",
                    help="имя BGP-протокола — только для лога")
    ap.add_argument("--fail-threshold", type=int, default=3)
    ap.add_argument("--ok-threshold", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--state", default="/var/lib/bgp-announcer/guard.state")
    args = ap.parse_args()

    st = load_state(args.state)
    ok = probe(args.socks_port, args.url, args.expect, args.timeout)

    if ok:
        st["fails"] = 0
        st["oks"] += 1
    else:
        st["oks"] = 0
        st["fails"] += 1

    if not st["withdrawn"] and st["fails"] >= args.fail_threshold:
        st["withdrawn"] = True
        st["fails"] = 0
        print("[!] туннель мёртв — анонсы снимаются (BGP-сессия сохраняется)")
    elif st["withdrawn"] and st["oks"] >= args.ok_threshold:
        st["withdrawn"] = False
        st["oks"] = 0
        print("[+] туннель ожил — анонсы возвращаются")

    # Приводим факт к желаемому: переживает рестарт BIRD и birdc configure,
    # который поднимает протокол заново.
    actual = bird_proto_state(args.protocol)
    if actual is None:
        print(f"[!] протокол {args.protocol} не найден в BIRD", file=sys.stderr)
    elif (actual == "down") != st["withdrawn"]:
        verb = "disable" if st["withdrawn"] else "enable"
        if birdc(f"{verb} {args.protocol}"):
            print(f"[*] birdc {verb} {args.protocol}: состояние приведено к нужному")

    save_state(args.state, st)
    print(f"probe={'ok' if ok else 'fail'} fails={st['fails']} oks={st['oks']} "
          f"announce={'off' if st['withdrawn'] else 'on'} "
          f"bgp={bird_proto_state(args.bgp_protocol)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
