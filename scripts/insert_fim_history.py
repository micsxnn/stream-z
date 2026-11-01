#!/usr/bin/env python3
"""One-shot: insere marcadores «fim» nas fronteiras de turno históricas do feed.

Fronteiras (texto inicial do item que ENCERRA o turno):
  - "Você tá certo"  -> fim da resposta final do turno da política v1
  - "position:fixed sem compensar" -> fim da narrativa do turno interrompido
  - "É isso —"       -> fim da resposta final do turno do visual v2
Idempotente: pula fronteiras que já têm fim logo em seguida.
"""
import json
import os
import urllib.request

CONF = "/home/z/my-project/.secrets/mirror.json"
BOUNDARIES = [
    "Você tá certo",
    "position:fixed sem compensar",
    "É isso —",
]

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
    token = os.environ["GH_TOKEN"]
    gid = json.load(open(CONF))["gist_id"]
    gist = api(f"https://api.github.com/gists/{gid}", "GET", token)
    feed = json.loads(gist["files"]["feed.json"]["content"])
    items = feed["items"]

    out, inserted = [], 0
    for i, it in enumerate(items):
        out.append(it)
        x = str(it.get("x", ""))
        for b in BOUNDARIES:
            if x.startswith(b):
                nxt = items[i + 1] if i + 1 < len(items) else None
                if not (nxt and nxt.get("k") == "fim"):
                    out.append({"t": it["t"], "k": "fim", "x": "fim"})
                    inserted += 1
                break

    if not inserted:
        print("nada a inserir")
        return
    feed["items"] = out
    api(f"https://api.github.com/gists/{gid}", "PATCH", token,
        {"files": {"feed.json": {"content": json.dumps(feed, ensure_ascii=False)}}})
    print(f"ok :: {inserted} «fim» históricos inseridos :: {len(out)} itens no feed")

if __name__ == "__main__":
    main()
