#!/usr/bin/env python3
"""mirror_push.py — transmite uma fala para o stream-z (feed ao vivo).

O stream-z é um feed JSON hospedado num gist SECRETO do GitHub:
    feed.json = {"updated": "<iso>", "items": [{"t": "<iso>", "k": "<kind>", "x": "<texto>"}]}

POLÍTICA DE OPERAÇÃO (regra de ouro do stream-z):
  1. TODO texto que o agente falar no chat vai PRIMEIRO para o stream-z, verbatim,
     e DEPOIS aparece no chat — incluindo narrativas intermediárias entre tool calls.
  2. Ao TERMINAR cada turno:  --kind fim --text "fim"   (desenha o marcador «F I M»).
  3. Mensagens do USUÁRIO NUNCA vão para o stream-z (privacidade).

Uso:
    export GH_TOKEN=ghp_...                # token GitHub com escopo gist
    python3 mirror_push.py --kind agent --text "fala exata do agente"
    python3 mirror_push.py --kind fim --text "fim"

Identificação do gist (nesta ordem):
    --gist <id>   |   variável de ambiente GIST_ID   |   .secrets/mirror.json
    (.secrets/mirror.json é procurado na raiz da skill e em ~/.secrets/)

kinds: user | agent | status | tool | fim
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

API_URL = "https://api.github.com/gists/{gid}"
FEED_FILE = "feed.json"
MAX_ITEMS = 400          # máximo de itens no feed
MAX_BYTES = 400_000      # teto aproximado do payload do gist
RETRIES = 3


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def resolve_gist(explicit):
    if explicit:
        return explicit
    env = os.environ.get("GIST_ID")
    if env:
        return env
    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for path in (os.path.join(skill_root, ".secrets", "mirror.json"),
                 os.path.expanduser("~/.secrets/mirror.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)["gist_id"]
        except (OSError, KeyError, ValueError):
            continue
    sys.exit("erro: gist não informado (use --gist, GIST_ID ou .secrets/mirror.json)")


def http_json(url, token, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method="PATCH" if data else "GET")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    if data:
        req.add_header("Content-Type", "application/json")
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code in (409, 500, 502, 503, 504) and attempt < RETRIES:
                time.sleep(1.5 * attempt)
                continue
            sys.exit("erro HTTP {} na API do GitHub: {}".format(exc.code, body[:300]))
        except urllib.error.URLError as exc:
            last_err = exc
            if attempt < RETRIES:
                time.sleep(1.5 * attempt)
                continue
            sys.exit("erro de rede: {}".format(last_err))


def main() -> None:
    ap = argparse.ArgumentParser(description="Push de fala para o stream-z")
    ap.add_argument("--kind", default="agent",
                    choices=["user", "agent", "status", "tool", "fim"])
    ap.add_argument("--text", required=True, help="texto verbatim a transmitir")
    ap.add_argument("--gist", help="id do gist (senão: GIST_ID ou .secrets/mirror.json)")
    args = ap.parse_args()

    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("erro: GH_TOKEN não definido no ambiente")
    gid = resolve_gist(args.gist)

    gist = http_json(API_URL.format(gid=gid), token)
    raw = (gist.get("files") or {}).get(FEED_FILE, {}).get("content") or "{}"
    try:
        feed = json.loads(raw)
    except ValueError:
        feed = {"updated": "", "items": []}
    items = feed.get("items") or []
    items.append({"t": now_iso(), "k": args.kind, "x": args.text})
    items = items[-MAX_ITEMS:]
    feed = {"updated": now_iso(), "items": items}
    content = json.dumps(feed, ensure_ascii=False)
    while len(content.encode("utf-8")) > MAX_BYTES and len(items) > 1:
        items = items[1:]
        feed["items"] = items
        content = json.dumps(feed, ensure_ascii=False)

    http_json(API_URL.format(gid=gid), token,
              {"files": {FEED_FILE: {"content": content}}})
    print("ok: +1 item ({}); feed com {} itens, {} bytes".format(
        args.kind, len(items), len(content.encode("utf-8"))))


if __name__ == "__main__":
    main()
