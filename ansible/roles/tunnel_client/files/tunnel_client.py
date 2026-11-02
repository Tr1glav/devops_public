#!/usr/bin/env python3
"""
tunnel-pc — клиент пула Tunnel (api.tunnel.pw) для Linux.

Декомпилирован из Tunnel v0.22.0 (github.com/hussaroff/tunnel):
  - логин:  POST /v1/auth/login (username) или /v1/auth/login/email (email)
            -> access_token (Bearer)
  - пул:    GET /v2/servers?limit=N -> [{config_uri, protocol, health_status, ...}]
            (эндпоинт api/v3/configs из приложения больше не существует)
  - чек:    TCP ping на ноду (диагностика) + route proof через generate_204
            с проверкой статуса и egress-IP (аналог их TUN traffic proof)

Команды:
  fetch          логин + скачать конфиги в configs.json
  check          проверить конфиги (TCP ping + HTTP через Xray), ранжировать
  run --proxy    поднять локальный SOCKS5/HTTP-прокси на лучшем конфиге
  run --tun      поднять системный TUN (нужен sudo)
  best           fetch + check + run (всё сразу)

Креды: файл ~/.tunnel-creds (chmod 600):
  LOGIN=твой_логин
  PASSWORD=твой_пароль
"""

import argparse
import base64
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.abspath(__file__))
XRAY = os.path.join(BASE, "xray-bin", "xray")
API = "https://api.tunnel.pw"
UA = "tunnel-pc/1.0"
CREDS = os.environ.get("TUNNEL_CREDS", os.path.expanduser("~/.tunnel-creds"))
# Кэш токена: без него каждый логин создаёт новую сессию на бэкенде
# (в приложении видно как «30+ устройств») — поэтому token.json (0600)
TOKEN_FILE = os.environ.get("TUNNEL_TOKEN", os.path.join(BASE, "token.json"))
CONFIGS = os.path.join(BASE, "configs.json")
WORKDIR = os.path.join(BASE, "work")

# route proof URL'ы — те же, что в приложении (p094q2/g.java, h())
TEST_URLS = [
    ("https://www.gstatic.com/generate_204", 204),
    ("https://cp.cloudflare.com/generate_204", 204),
]
EGRESS_URL = "https://api.ipify.org"

TCP_TIMEOUT = 3.0
HTTP_TIMEOUT = 10


# ---------------------------------------------------------------- credentials

def read_creds():
    if not os.path.exists(CREDS):
        sys.exit(f"Нет файла {CREDS}. Создай:\n"
                 f"  printf 'LOGIN=...\\nPASSWORD=...\\n' > ~/.tunnel-creds && chmod 600 ~/.tunnel-creds")
    creds = {}
    with open(CREDS) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()
    if "LOGIN" not in creds or "PASSWORD" not in creds:
        sys.exit(f"В {CREDS} нужны LOGIN= и PASSWORD=")
    return creds


# -------------------------------------------------------------------- api calls

def http_json(method, url, body=None, token=None, timeout=30):
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read()[:300].decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code} {url}: {detail}") from e


def api_login(login, password):
    # Два эндпоинта (RE o1.java): /v1/auth/login — username ^[A-Za-z0-9_-]+$,
    # /v1/auth/login/email — email. Выбираем по формату логина.
    if "@" in login:
        path, body = "/v1/auth/login/email", {"email": login, "password": password}
    else:
        path, body = "/v1/auth/login", {"login": login, "password": password}
    j = http_json("POST", API + path, body)
    if "access_token" not in j:
        sys.exit(f"Логин не удался: {json.dumps(j, ensure_ascii=False)[:300]}")
    return j


def _load_token():
    try:
        with open(TOKEN_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _save_token(auth):
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump({"access_token": auth["access_token"],
                       "refresh_token": auth.get("refresh_token", "")}, f)
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass  # кэш токена не критичен


def api_auth(login, password):
    """(token, subscription_type) — без нового логина, если есть валидный кэш.

    Каждый логин создаёт на бэкенде новую сессию (в приложении — «устройство»),
    поэтому: 1) пробуем кэшированный access_token (GET /v1/me),
    2) пробуем refresh (POST /v1/auth/refresh), 3) только потом — логин.
    """
    t = _load_token()
    if t and t.get("access_token"):
        try:
            me = http_json("GET", API + "/v1/me", token=t["access_token"])
            return t["access_token"], (me or {}).get("subscription_type")
        except RuntimeError:
            pass
    if t and t.get("refresh_token"):
        try:
            auth = http_json("POST", API + "/v1/auth/refresh",
                             {"refresh_token": t["refresh_token"]})
            if "access_token" in auth:
                _save_token(auth)
                return auth["access_token"], auth.get("subscription_type")
        except RuntimeError:
            pass
    auth = api_login(login, password)
    _save_token(auth)
    return auth["access_token"], auth.get("subscription_type")


def fetch_configs(verbose=True):
    creds = read_creds()
    if verbose:
        print(f"[*] Auth: {creds['LOGIN']}")
    token, sub_type = api_auth(creds["LOGIN"], creds["PASSWORD"])
    if verbose and sub_type:
        print(f"    subscription_type: {sub_type}")
    # Пул: GET /v2/servers (эндпоинт api/v3/configs из приложения больше не существует, 404)
    j = http_json("GET", API + "/v2/servers?limit=200", token=token)
    servers = j if isinstance(j, list) else (j.get("data") or j.get("servers") or [])
    if not isinstance(servers, list):
        sys.exit(f"Неожиданный формат ответа servers: {str(j)[:300]}")
    configs = []
    for s in servers:
        if not isinstance(s, dict):
            continue
        if s.get("access_allowed") is False:
            continue
        if s.get("provision_status") not in (None, "ready"):
            continue
        uri = s.get("config_uri") or s.get("raw_uri") or s.get("vless_uri")
        if uri:
            configs.append(uri)
    os.makedirs(WORKDIR, exist_ok=True)
    with open(CONFIGS, "w") as f:
        json.dump({"fetched_at": time.time(),
                   "subscription_type": sub_type,
                   "configs": configs}, f)
    if verbose:
        print(f"[*] Получено конфигов: {len(configs)} -> {CONFIGS}")
    return configs


def load_configs():
    if not os.path.exists(CONFIGS):
        sys.exit(f"Нет {CONFIGS} — сначала: {sys.argv[0]} fetch")
    with open(CONFIGS) as f:
        j = json.load(f)
    return j["configs"]


# ------------------------------------------------------------------ uri parsing

def b64url_decode(s):
    s = s.replace("-", "+").replace("_", "/")
    s += "=" * (-len(s) % 4)
    return base64.b64decode(s)


def parse_uri(uri):
    """Возвращает dict с полями для Xray outbound или None, если протокол не поддерживаем."""
    u = uri.strip()
    if u.startswith("vless://"):
        return parse_vless(u)
    if u.startswith("vmess://"):
        return parse_vmess(u)
    if u.startswith("trojan://"):
        return parse_trojan(u)
    if u.startswith("ss://"):
        return parse_ss(u)
    # Xray 26.10.21 не имеет outbound hysteria2 (только hysteria v1) — пропускаем
    if u.startswith(("hysteria2://", "hy2://")):
        return None
    if u.startswith("tuic://"):
        return parse_tuic(u)
    return None


def host_port_from(uri_after_scheme):
    # user:pass@host:port?query#frag
    frag = ""
    if "#" in uri_after_scheme:
        uri_after_scheme, frag = uri_after_scheme.rsplit("#", 1)
    query = ""
    if "?" in uri_after_scheme:
        uri_after_scheme, query = uri_after_scheme.split("?", 1)
    params = dict(urllib.parse.parse_qsl(query))
    if "@" in uri_after_scheme:
        userinfo, hostpart = uri_after_scheme.rsplit("@", 1)
    else:
        userinfo, hostpart = "", uri_after_scheme
    if ":" in hostpart:
        host, port = hostpart.rsplit(":", 1)
    else:
        host, port = hostpart, "443"
    return userinfo, host, int(port), params, frag


def parse_vless(u):
    userinfo, host, port, p, frag = host_port_from(u[len("vless://"):])
    uuid = userinfo
    net = p.get("type", "tcp")
    sec = p.get("security", "none")
    out = {
        "protocol": "vless",
        "address": host, "port": port,
        "remark": frag or host,
        "users": [{"id": uuid, "encryption": p.get("encryption", "none")}],
        "stream": {"network": net, "security": sec},
    }
    if p.get("flow"):
        out["users"][0]["flow"] = p["flow"]
    st = out["stream"]
    if sec == "reality":
        st["realitySettings"] = {
            "serverName": p.get("sni", ""),
            "fingerprint": p.get("fp", "chrome"),
            "publicKey": p.get("pbk", ""),
            "shortId": p.get("sid", ""),
            "spiderX": p.get("spx", ""),
        }
    elif sec == "tls":
        st["tlsSettings"] = {"serverName": p.get("sni", "")}
        if p.get("fp"):
            st["tlsSettings"]["fingerprint"] = p["fp"]
    if net == "ws":
        st["wsSettings"] = {"path": p.get("path", "/")}
        if p.get("host"):
            st["wsSettings"]["headers"] = {"Host": p["host"]}
    elif net == "grpc":
        st["grpcSettings"] = {"serviceName": p.get("serviceName", "")}
    elif net in ("http", "httpupgrade"):
        st["httpupgradeSettings"] = {"path": p.get("path", "/")}
    elif net in ("xhttp", "splithttp"):
        # Xray XHTTP (в ядре splithttp, network "xhttp" — алиас):
        # xhttpSettings {mode: auto|stream-one|stream-up, path, host, xPaddingBytes: "N-M"}
        xs = {"mode": p.get("mode", "auto"), "path": p.get("path", "/")}
        if p.get("host"):
            xs["host"] = p["host"]
        xpad = p.get("x_padding_bytes") or p.get("xPaddingBytes")
        if xpad:
            xs["xPaddingBytes"] = xpad
        st["xhttpSettings"] = xs
    return out


def parse_vmess(u):
    raw = u[len("vmess://"):]
    try:
        j = json.loads(b64url_decode(raw))
    except (ValueError, TypeError):
        return None
    net = j.get("net", "tcp")
    sec = "tls" if j.get("tls") else "none"
    out = {
        "protocol": "vmess",
        "address": j.get("add"), "port": int(j.get("port", 443)),
        "remark": j.get("ps") or j.get("add"),
        "users": [{"id": j.get("id"), "alterId": int(j.get("aid", 0)),
                   "security": j.get("scy", "auto")}],
        "stream": {"network": net, "security": sec},
    }
    if sec == "tls":
        st = {"serverName": j.get("sni", "")}
        if j.get("fp"):
            st["fingerprint"] = j["fp"]
        out["stream"]["tlsSettings"] = st
    if net == "ws":
        out["stream"]["wsSettings"] = {"path": j.get("path", "/")}
        if j.get("host"):
            out["stream"]["wsSettings"]["headers"] = {"Host": j["host"]}
    elif net == "grpc":
        out["stream"]["grpcSettings"] = {"serviceName": j.get("path", "")}
    return out


def parse_trojan(u):
    userinfo, host, port, p, frag = host_port_from(u[len("trojan://"):])
    out = {
        "protocol": "trojan",
        "address": host, "port": port,
        "remark": frag or host,
        "users": [{"password": userinfo}],
        "stream": {"network": p.get("type", "tcp"), "security": "tls"},
    }
    st = {"serverName": p.get("sni", "")}
    if p.get("fp"):
        st["fingerprint"] = p["fp"]
    out["stream"]["tlsSettings"] = st
    if out["stream"]["network"] == "ws":
        out["stream"]["wsSettings"] = {"path": p.get("path", "/")}
    return out


def parse_ss(u):
    raw = u[len("ss://"):]
    frag = ""
    if "#" in raw:
        raw, frag = raw.rsplit("#", 1)
    if "@" in raw:
        b64part, hostpart = raw.rsplit("@", 1)
    else:
        b64part, hostpart = raw, ""
    userinfo = b64url_decode(b64part)
    if ":" not in userinfo:
        return None
    method, password = userinfo.split(":", 1)
    if ":" in hostpart:
        host, port = hostpart.rsplit(":", 1)
    else:
        host, port = hostpart, "8388"
    return {
        "protocol": "shadowsocks",
        "address": host, "port": int(port),
        "remark": frag or host,
        "method": method,
        "password": password,
        "stream": {},
    }


def parse_tuic(u):
    userinfo, host, port, p, frag = host_port_from(u[len("tuic://"):])
    uuid, _, password = userinfo.partition(":")
    out = {
        "protocol": "tuic",
        "address": host, "port": port,
        "remark": frag or host,
        "users": [{"uuid": uuid, "password": password}],
        "stream": {},
    }
    if p.get("sni"):
        out["sni"] = p["sni"]
    if p.get("alpn"):
        out["alpn"] = p["alpn"].split(",")
    if p.get("insecure") in ("1", "true"):
        out["insecure"] = True
    return out


# ---------------------------------------------------------------- xray config

def build_outbound(parsed):
    proto = parsed["protocol"]
    ob = {"tag": "proxy", "protocol": proto,
          "settings": {}, "streamSettings": parsed.get("stream", {})}
    st = ob["streamSettings"]

    if proto in ("vless", "vmess"):
        ob["settings"] = {"vnext": [{
            "address": parsed["address"], "port": parsed["port"],
            "users": parsed["users"]}]}
    elif proto == "trojan":
        ob["settings"] = {"servers": [{
            "address": parsed["address"], "port": parsed["port"],
            "password": parsed["users"][0]["password"]}]}
    elif proto == "shadowsocks":
        ob["settings"] = {"servers": [{
            "address": parsed["address"], "port": parsed["port"],
            "method": parsed["method"], "password": parsed["password"]}]}
        ob["streamSettings"] = {}
    elif proto == "tuic":
        ob["settings"] = {"servers": [{
            "address": parsed["address"], "port": parsed["port"],
            "uuid": parsed["users"][0]["uuid"],
            "password": parsed["users"][0]["password"]}]}
        tls = {}
        if parsed.get("sni"):
            tls["serverName"] = parsed["sni"]
        if parsed.get("alpn"):
            tls["alpn"] = parsed["alpn"]
        if parsed.get("insecure"):
            tls["allowInsecure"] = True
        st.update({"security": "tls", "tlsSettings": tls})
    return ob


def xray_config(outbound, mode, socks_port=10808, http_port=10809, tproxy_port=None):
    inbounds = []
    if mode == "proxy":
        inbounds = [
            {"tag": "socks-in", "port": socks_port, "protocol": "socks",
             "settings": {"udp": True},
             "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}},
            {"tag": "http-in", "port": http_port, "protocol": "http"},
        ]
        if tproxy_port:
            # Прозрачный inbound для TPROXY (транзитный трафик с других хостов).
            # followRedirect=true ОБЯЗАТЕЛЕН: включает ReceiveOriginalDestination
            # (infra/conf/xray.go), ядро отдаёт оригинальный dest через
            # IP_RECVORIGDSTADDR/SO_ORIGINAL_DST, и routing решает direct
            # (geoip:private) или туннель. Поля followOriginalDestination в
            # Xray 26.10.21 нет — оно молча игнорировалось.
            # sockopt.tproxy ОБЯЗАТЕЛЕН: без него Xray не ставит IP_TRANSPARENT
            # на сокет, и ядро не доставляет TPROXY-маркированные пакеты.
            # ВАЖНО: sockopt читается ТОЛЬКО из streamSettings.sockopt
            # (infra/conf/xray.go: StreamConfig.SocketSettings json:"sockopt").
            inbounds.append({
                "tag": "tproxy-in", "port": tproxy_port, "protocol": "dokodemo-door",
                "settings": {"address": "127.0.0.1", "port": 25,
                             "network": "tcp,udp",
                             "followRedirect": True},
                "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
                "streamSettings": {"sockopt": {"tproxy": "tproxy"}},
            })
    else:  # tun
        inbounds = [
            {"tag": "tun-in", "protocol": "tun",
             "address": ["172.19.0.1/8"], "mtu": 1500, "stack": "system",
             "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}},
        ]
    rules = [{"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"}]
    return {
        "log": {"loglevel": "warning"},
        "inbounds": inbounds,
        "outbounds": [outbound, {"protocol": "freedom", "tag": "direct"},
                      {"protocol": "blackhole", "tag": "block"}],
        "routing": {"domainStrategy": "AsIs", "rules": rules},
    }


# ---------------------------------------------------------------------- checks

def tcp_ping(host, port, timeout=TCP_TIMEOUT):
    t0 = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, (time.time() - t0) * 1000
    except OSError:
        return False, (time.time() - t0) * 1000


def curl_via_proxy(url, proxy, timeout=HTTP_TIMEOUT):
    """curl через SOCKS5; возвращает (http_code, time_total_s) или (None, err)."""
    cmd = ["curl", "-s", "-o", "/dev/null",
           "-w", "%{http_code} %{time_total}",
           "--socks5-hostname", f"127.0.0.1:{proxy}",
           "--max-time", str(timeout), url]
    try:
        r = subprocess.run(cmd, check=False, capture_output=True,
                           text=True, timeout=timeout + 3)
        code, t = r.stdout.split()
        return int(code), float(t)
    except (subprocess.SubprocessError, OSError, ValueError) as e:
        return None, str(e)


def check_one(parsed, idx):
    """Полная проверка: Xray на unique-порту + route proof. Возвращает dict."""
    socks_port = 12000 + idx
    cfg = xray_config(build_outbound(parsed), "proxy", socks_port=socks_port,
                      http_port=socks_port + 1000)
    cfgfile = os.path.join(WORKDIR, f"check-{idx}.json")
    logf = os.path.join(WORKDIR, f"check-{idx}.log")
    with open(cfgfile, "w") as f:
        json.dump(cfg, f)
    log = open(logf, "w")  # noqa: SIM115 — файл живёт, пока работает процесс
    proc = subprocess.Popen([XRAY] + run_args(cfgfile),
                            stdout=log, stderr=subprocess.STDOUT)
    try:
        # ждём, пока поднимется локальный прокси
        ok = False
        for _ in range(40):
            time.sleep(0.1)
            try:
                with socket.create_connection(("127.0.0.1", socks_port), timeout=0.3):
                    ok = True
                    break
            except OSError:
                if proc.poll() is not None:
                    break
        if not ok:
            return {"ok": False, "stage": "xray_start",
                    "detail": read_tail(logf)}
        # route proof: те же URL, что в приложении
        results = []
        for url, expect in TEST_URLS:
            code, t = curl_via_proxy(url, socks_port)
            results.append((url, code, t))
            if code == expect:
                break
        if not any(c == e for (u, c, t), (uu, e) in zip(results, TEST_URLS)):
            return {"ok": False, "stage": "route_proof", "results": results,
                    "detail": read_tail(logf)}
        # egress IP (аналог TUN traffic proof: трафик реально уходит с сервера)
        egress = None
        try:
            cmd = ["curl", "-s", "--socks5-hostname", f"127.0.0.1:{socks_port}",
                   "--max-time", "8", EGRESS_URL]
            egress = subprocess.run(cmd, check=False, capture_output=True,
                                    text=True, timeout=11).stdout.strip()
        except (subprocess.SubprocessError, OSError):
            egress = None  # без egress вердикт всё равно выносим по route proof
        # берём задержку первого успешного URL
        ok_res = next(((c, t) for (u, c, t), (uu, e) in zip(results, TEST_URLS) if c == e),
                      (results[0][1], results[0][2]))
        return {"ok": True, "stage": "done",
                "latency_ms": round(ok_res[1] * 1000, 1), "egress_ip": egress,
                "results": results}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def read_tail(path, n=400):
    try:
        with open(path) as f:
            return f.read()[-n:]
    except OSError:
        return ""


def run_args(cfgfile):
    return ["-c", cfgfile]


# ----------------------------------------------------------------------- check

def cmd_check(limit=None, full_limit=40):
    configs = load_configs()
    if limit:
        configs = configs[:limit]
    parsed_list = []
    for i, uri in enumerate(configs):
        p = parse_uri(uri)
        if p is None:
            print(f"[{i:2d}] SKIP (не поддержанный формат): {uri[:80]}")
            continue
        parsed_list.append((i, p))

    print(f"[*] TCP ping {len(parsed_list)} нод (параллельно)...")
    alive = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(tcp_ping, p["address"], p["port"]): (i, p)
                for i, p in parsed_list}
        for f in as_completed(futs):
            i, p = futs[f]
            ok, ms = f.result()
            mark = "OK " if ok else "DEAD"
            print(f"    [{i:2d}] {mark} {p['protocol']:10s} {p['address']}:{p['port']} "
                  f"({ms:.0f} мс)  {p['remark'][:40]}")
            if ok:
                alive.append((i, p, ms))

    if not alive:
        sys.exit("Ни одна нода не ответила на TCP ping.")

    # Пул большой, полная проверка медленная (~3с/нода) — берём топ по TCP-задержке
    alive.sort(key=lambda x: x[2])
    to_check = alive[:full_limit] if full_limit else alive
    print(f"[*] Route proof через Xray: {len(to_check)} нод "
          f"(топ по TCP-задержке, последовательно)...")
    good = []
    for n, (i, p, tcp_ms) in enumerate(to_check):
        r = check_one(p, n)
        name = f"{p['protocol']} {p['address']}:{p['port']} {p['remark'][:30]}"
        if r["ok"]:
            egress = r.get("egress_ip") or "?"
            print(f"    [{i:2d}] WORKS  {r['latency_ms']:7.1f} мс  egress={egress}  {name}")
            good.append((r["latency_ms"], i, p, tcp_ms))
        else:
            print(f"    [{i:2d}] FAIL   stage={r['stage']}  {name}")
            if r.get("detail"):
                print(f"             {r['detail'][:160].strip()}")

    good.sort()
    if good:
        print("\n=== Топ рабочих (по задержке) ===")
        for lat, i, p, tcp_ms in good[:10]:
            print(f"  {lat:7.1f} мс  [{i:2d}] {p['protocol']} {p['address']}:{p['port']} {p['remark'][:40]}")
        os.makedirs(WORKDIR, exist_ok=True)
        with open(os.path.join(WORKDIR, "ranking.json"), "w") as f:
            json.dump([{"index": i, "uri": configs[i], "latency_ms": lat}
                       for lat, i, p, tcp_ms in good], f, indent=1)
        return good
    sys.exit("Нет рабочих нод.")


# ------------------------------------------------------------------------ run

def cmd_run(mode, proxy_idx=None):
    ranking = os.path.join(WORKDIR, "ranking.json")
    if proxy_idx is None and os.path.exists(ranking):
        with open(ranking) as f:
            ranking_j = json.load(f)
        if ranking_j:
            proxy_idx = ranking_j[0]["index"]
            print(f"[*] Берём лучшую из проверки: [{proxy_idx}]")
    if proxy_idx is None:
        sys.exit("Укажи индекс: run --proxy --idx N (или сначала check)")
    configs = load_configs()
    p = parse_uri(configs[proxy_idx])
    if p is None:
        sys.exit(f"Конфиг [{proxy_idx}] не распарсился: {configs[proxy_idx][:80]}")

    if mode == "tun" and os.geteuid() != 0:
        sys.exit("TUN-режим нужен sudo: sudo python3 tunnel_pc.py run --tun")

    # TPROXY-порт (транзит): задаётся окружением (systemd), на ПК не задан
    tproxy_port = int(os.environ["TUNNEL_TPROXY_PORT"]) \
        if os.environ.get("TUNNEL_TPROXY_PORT") else None
    cfg = xray_config(build_outbound(p), mode, tproxy_port=tproxy_port)
    cfgfile = os.path.join(WORKDIR, "run.json")
    with open(cfgfile, "w") as f:
        json.dump(cfg, f)
    name = f"{p['protocol']} {p['address']}:{p['port']} {p['remark'][:40]}"
    if mode == "proxy":
        extra = f", TPROXY 127.0.0.1:{tproxy_port}" if tproxy_port else ""
        print(f"[*] Xray proxy: SOCKS5 127.0.0.1:10808, HTTP 127.0.0.1:10809{extra}")
        print(f"    нода: {name}")
        print("    Ctrl+C для остановки")
    else:
        print(f"[*] Xray TUN (system-wide): нода {name}")
        print("    Ctrl+C для остановки")
    try:
        rc = subprocess.run([XRAY, "-c", cfgfile], check=False).returncode
    except KeyboardInterrupt:
        print("\n[*] Остановлено")
        return
    # Не ноль -> systemd (Restart=on-failure) перезапустит best --proxy:
    # перепроверит пул и поднимет туннель на другой ноде
    if rc != 0:
        sys.exit(f"Xray завершился с кодом {rc}")


# ----------------------------------------------------------------------- best

def cmd_best(mode, limit=None, full_limit=40):
    fetch_configs()
    good = cmd_check(limit=limit, full_limit=full_limit)
    if good:
        cmd_run(mode, proxy_idx=good[0][1])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("fetch")
    c = sub.add_parser("check")
    c.add_argument("--limit", type=int)
    c.add_argument("--full-limit", type=int, default=40,
                   help="сколько нод проверять полностью (по умолчанию 40, 0 = все)")
    r = sub.add_parser("run")
    r.add_argument("--proxy", action="store_true")
    r.add_argument("--tun", action="store_true")
    r.add_argument("--idx", type=int)
    b = sub.add_parser("best")
    b.add_argument("--proxy", action="store_true", default=True)
    b.add_argument("--tun", action="store_true")
    b.add_argument("--limit", type=int)
    b.add_argument("--full-limit", type=int, default=40)
    a = ap.parse_args()

    if a.cmd == "fetch":
        fetch_configs()
    elif a.cmd == "check":
        cmd_check(a.limit, a.full_limit)
    elif a.cmd == "run":
        mode = "tun" if a.tun else "proxy"
        cmd_run(mode, a.idx)
    elif a.cmd == "best":
        cmd_best("tun" if a.tun else "proxy", a.limit, a.full_limit)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
