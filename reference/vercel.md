# Caminho A — Viewer na Vercel (link fixo)

Arquivos de origem: `assets/viewer.html` → vira `index.html`; `assets/feed.js` → vira
`api/feed.js`. O mesmo gist alimenta o feed; a Vercel só hospeda o site + o proxy.

## 1. Pegue o token VERCEL do usuário (escopo Full Account — obrigatório)

Oriente o usuário passo a passo com este texto:

> 1. Entre em https://vercel.com e faça login na sua conta.
> 2. Clique no seu avatar (canto superior direito) → **Account Settings**.
> 3. No menu lateral, aba **Tokens** → botão **Create**.
> 4. Preencha: nome `stream-z`; **Scope: Full Account** (⚠️ não escolha projeto
>    específico — sem Full Account o deploy pela CLI falha); Expiration: o menor
>    que atender.
> 5. Clique em Create, COPIE o token (começa com `vcp_` — ele só aparece uma vez)
>    e cole aqui no chat.

## 2. Pegue o token GITHUB do usuário (escopo gist)

> 1. Entre em https://github.com → foto de perfil → **Settings**.
> 2. No rodapé do menu lateral: **Developer settings**.
> 3. **Personal access tokens → Tokens (classic)** → **Generate new token (classic)**.
> 4. Nome `stream-z`, marque SOMENTE o escopo **gist**, depois Generate.
> 5. Copie o token (começa com `ghp_` — aparece uma vez só) e cole aqui no chat.

Salve os dois em `.secrets/tokens.env` na sandbox (pasta `700`, arquivos `600`, nunca em git):

```
GH_TOKEN=ghp_...
VERCEL_TOKEN=vcp_...
```

## 3. Monte a pasta e crie o gist (banco do feed)

```bash
mkdir -p stream-z/api
cp <caminho-da-skill>/assets/viewer.html stream-z/index.html
cp <caminho-da-skill>/assets/feed.js    stream-z/api/feed.js
set -a && source .secrets/tokens.env && set +a
curl -s -X POST -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" https://api.github.com/gists \
  -d '{"public":false,"files":{"feed.json":{"content":"{\"updated\":\"\",\"items\":[]}"}}}'
```

Guarde o `"id"` da resposta em `.secrets/mirror.json` como `{"gist_id":"..."}` —
o proxy (`api/feed.js`) lê esse id da **env var `GIST_ID`** (registrada na Vercel no
passo 4); nada de gist ou token vai hardcoded em código.

## 4. Suba na Vercel

```bash
cd stream-z
# 1º deploy: cria e liga o projeto (nome = nome da pasta)
npx -y vercel deploy --prod --yes --token "$VERCEL_TOKEN"
# registra as env vars do proxy (valores via stdin)
printf "%s" "$GH_TOKEN"  | npx -y vercel env add GH_TOKEN production --token "$VERCEL_TOKEN"
printf "%s" "$GIST_ID"   | npx -y vercel env add GIST_ID  production --token "$VERCEL_TOKEN"
# 2º deploy: a variável passa a valer
npx -y vercel deploy --prod --yes --token "$VERCEL_TOKEN"
```

O link sai no final (ex.: `https://stream-z.vercel.app`). Renomear o projeto ou usar
domínio próprio é opcional (dashboard → Settings → Domains).

## 5. Acenda o stream-z

```bash
python3 <caminho-da-skill>/scripts/mirror_push.py --kind status --text "stream-z no ar"
```

Abra o site: a linha aparece em até 2,5 s e o skeleton para de girar. Combine com o
usuário: a partir de AGORA vale a Regra de Ouro (SKILL.md).
