#!/usr/bin/env python3
"""Espelho-z: empurra uma mensagem para o feed ao vivo (gist).

POLÍTICA (acordo com o usuário, revisada em 2026-11-01):
  - TODA fala do agente vai para o espelho VERBATIM e ANTES de aparecer no
    chat — incluindo as narrativas intermediárias entre tool calls, não só
    a mensagem final. Cada parágrafo de narrativa: push primeiro, depois o
    mesmo texto no chat.
      python3 mirror_push.py --kind agent --text "<fala exata>"
  - Mensagens do USUÁRIO não vão para o site (privacidade), a não ser que ele peça.
  - kinds: user | agent | status | tool | fim
  - Ao TERMINAR cada turno, marque o fim da transmissão no site (o marcador
    «fim» aparece no lugar do antigo footer, separando um turno do outro):
      python3 mirror_push.py --kind fim --text "fim"

Uso:
  python3 mirror_push.py --kind agent --text "texto da mensagem"
  python3 mirror_push.py --kind status --file /tmp/trecho.md
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request

CONF = "/home/z/my-project/.secrets/mirror.json"
MAX_ITEMS = 400
MAX_BYTES = 400_000


def api(url, method="GET", token=None, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "z-mirror")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, body) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="agent",
                    choices=["user", "agent", "status", "tool", "fim"])
    ap.add_argument("--text")
    ap.add_argument("--file")
    a = ap.parse_args()

    if not (a.text or a.file):
        sys.exit("informe --text ou --file")
    text = a.text if a.text else open(a.file, encoding="utf-8").read()
    text = text.strip()
    if not text:
        sys.exit("texto vazio")

    token = os.environ["GH_TOKEN"]
    conf = json.load(open(CONF))
    gid = conf["gist_id"]

    gist = api(f"https://api.github.com/gists/{gid}", "GET", token)
    raw = gist["files"]["feed.json"]["content"]
    feed = json.loads(raw)

    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    item = {"t": now, "k": a.kind, "x": text}
    feed["items"].append(item)
    feed["items"] = feed["items"][-MAX_ITEMS:]
    feed["updated"] = now
    while len(json.dumps(feed).encode()) > MAX_BYTES and len(feed["items"]) > 1:
        feed["items"] = feed["items"][1:]

    api(f"https://api.github.com/gists/{gid}", "PATCH", token,
        {"files": {"feed.json": {"content": json.dumps(feed, ensure_ascii=False)}}})
    print(f"push ok :: {len(feed['items'])} itens no feed :: ultimo {a.kind} @ {now}")


if __name__ == "__main__":
    main()
