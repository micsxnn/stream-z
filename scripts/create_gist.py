#!/usr/bin/env python3
"""create_gist.py — cria o gist secreto que serve de banco do stream-z (feed.json).

Grava a configuração em .secrets/mirror.json na raiz da skill (fora do git).

Uso:
    export GH_TOKEN=ghp_...    # token GitHub com escopo gist
    python3 scripts/create_gist.py
"""
import json
import os
import sys
import urllib.request

API = "https://api.github.com/gists"
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SKILL_ROOT, ".secrets", "mirror.json")


def api(url, method="GET", token=None, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "stream-z")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, body) as r:
        return json.load(r)


def main():
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("erro: GH_TOKEN não definido no ambiente (escopo gist)")
    feed = {"updated": "", "items": []}
    gist = api(
        API,
        "POST",
        token,
        {
            "description": "stream-z :: feed ao vivo",
            "public": False,
            "files": {"feed.json": {"content": json.dumps(feed)}},
        },
    )
    conf = {
        "gist_id": gist["id"],
        "raw_url": gist["files"]["feed.json"]["raw_url"],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(conf, f, indent=2)
    os.chmod(OUT, 0o600)
    print("gist_id:", conf["gist_id"])
    print("config salva em:", OUT)


if __name__ == "__main__":
    main()
