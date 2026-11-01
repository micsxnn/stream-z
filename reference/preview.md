# Caminho B — Viewer no preview da plataforma

O stream-z roda como um mini Next.js na sandbox: página estática + rota de API. O feed
continua no gist, então o histórico sobrevive a reciclagens de sessão.

## 1. Monte o projeto

Use o fluxo do fullstack-dev (Next.js). Depois:

```bash
mkdir -p app/api/feed public
cp <caminho-da-skill>/assets/viewer.html public/mirror.html
```

Crie `app/api/feed/route.ts`:

```ts
export const dynamic = "force-dynamic";
export async function GET() {
  const r = await fetch(`https://api.github.com/gists/${process.env.GIST_ID}`, {
    headers: { Authorization: `Bearer ${process.env.GH_TOKEN}`,
               Accept: "application/vnd.github+json" },
    cache: "no-store",
  });
  const body = r.ok
    ? (await r.json())?.files?.["feed.json"]?.content ?? '{"updated":"","items":[]}'
    : '{"updated":"","items":[]}';
  return new Response(body, { headers: {
    "content-type": "application/json", "cache-control": "no-store" } });
}
```

## 2. Rode com os tokens no ambiente

```bash
set -a && source .secrets/tokens.env && set +a
export GIST_ID=<id do gist>
# inicie o dev server do projeto herdando essas variáveis
```

## 3. ENCURTE o link antes de entregar (preview é gigante)

Serviço: **is.gd** — https://is.gd — API pública sem cadastro e sem chave; a resposta
vem em texto puro, pronta para mostrar ao usuário. Endpoint exato:

```
https://is.gd/create.php?format=simple&url=<URL_CODIFICADA>
```

```bash
curl -s "https://is.gd/create.php?format=simple&url=https%3A%2F%2Fpreview-SEU-BOT.space-z.ai%2Fmirror.html"
# → https://is.gd/xxxxxx
```

Limites: máx. 5 conexões simultâneas; se bater rate limit, espere ~1 minuto.

**Reservas** (se o is.gd falhar, mesma sintaxe): `https://v.gd/create.php?format=simple&url=…`
(mesmo serviço, outro domínio) e `https://tinyurl.com/api-create.php?url=…`.

Entregue ao usuário o link CURTO e o original. O viewer fica em `/mirror.html`.

## 4. Avisos ao usuário

- O preview vive enquanto a sessão vive. Sandbox reciclou ou o bot-id mudou? Suba de
  novo e re-encurte — o feed está no gist, nada se perde.
- A partir daqui vale a Regra de Ouro (SKILL.md).
