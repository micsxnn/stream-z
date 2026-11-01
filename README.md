# espelho-z :: transmissão ao vivo

Espelho independente da plataforma de chat: um site na Vercel que recebe **toda fala do agente antes de ela aparecer no chat**, para acompanhar em tempo real mesmo quando a plataforma travar.

## Como funciona

```
 agente (sandbox)                    github (gist secreto)            vercel
 ────────────────                    ─────────────────────            ──────
 mirror_push.py ──── PATCH ────▶  gist/feed.json ◀─── GET ────  api/feed.js
 (cada fala, verbatim,                                    (GH_TOKEN      │
  ANTES de aparecer no chat)                               no server)    ▼
                                                     index.html ◀── /api/feed
                                                     (poll 2,5 s, sem cache)
```

1. O agente empurra cada fala para um **gist secreto** (`feed.json`) com `scripts/mirror_push.py` — sempre **antes** de exibir a mensagem no chat (política do espelho).
2. O site (`index.html`) busca `/api/feed` a cada 2,5 s com `cache: no-store`.
3. A função serverless `api/feed.js` lê o gist **autenticado** com `GH_TOKEN` (env var na Vercel) — assim o CDN do gist nunca serve uma versão velha, e o token nunca chega ao navegador.
4. O feed trunca no máximo 400 itens / 400 KB (corta do começo).

## Protocolo do feed

```json
{"updated": "<ISO-8601>", "items": [{"t": "<ISO>", "k": "<kind>", "x": "<texto>"}]}
```

kinds: `user` | `agent` | `status` | `tool` | `fim` — o `fim` é o marcador de fim de turno: o agente manda um push ao terminar e o site desenha o «F I M» com fios em degradê (ocupa o lugar do antigo footer e separa os turnos).

## Arquivos

| Arquivo | Papel |
| --- | --- |
| `index.html` | Viewer: timeline, agrupamento por emissor (símbolo só no primeiro parágrafo do bloco, continuação ligada por fio vertical), chip ao vivo/reconectando/sem sinal, botão "ver novas mensagens", skeleton que imita as mensagens |
| `api/feed.js` | Proxy serverless de leitura autenticada do gist |
| `scripts/create_gist.py` | Cria o gist secreto e grava `.secrets/mirror.json` |
| `scripts/mirror_push.py` | Empurra uma mensagem para o feed (`--kind` + `--text`/`--file`) |
| `scripts/insert_fim_history.py` | One-shot: insere «fim» retroativo nas fronteiras históricas de turno |

## Deploy

```bash
# 1) criar o gist do feed (grava o gist_id em .secrets/mirror.json)
GH_TOKEN=ghp_... python3 scripts/create_gist.py

# 2) subir o site + api na Vercel (ou conectar este repo na Vercel p/ deploy automático)
cd stream-z  # raiz deste repo
npx vercel link
printf '%s' "$GH_TOKEN" | npx vercel env add GH_TOKEN production
npx vercel deploy --prod
```

## Segurança

- Tokens ficam em `.secrets/` (chmod 600, fora do git) e nas env vars da Vercel — **nunca** no código.
- O gist é secreto; a leitura pública passa pelo proxy `/api/feed`.
- Revogar os tokens ao fim do uso.
