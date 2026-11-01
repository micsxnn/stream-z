#!/usr/bin/env python3
"""Cria o gist secreto que serve de banco de dados do stream-z (feed.json)."""
import json
import os
import urllib.request

OUT = "/home/z/my-project/.secrets/mirror.json"
API = "https://api.github.com/gists"


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
    with open(OUT, "w") as f:
        json.dump(conf, f, indent=2)
    os.chmod(OUT, 0o600)
    print("gist_id:", conf["gist_id"])


if __name__ == "__main__":
    main()
