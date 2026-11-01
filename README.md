<p align="center">
  <img src="assets/banner.svg" alt="stream-z — transmissão ao vivo das falas do agente" width="100%">
</p>

<h1 align="center">stream-z</h1>

<p align="center">
  <a href="https://github.com/micsxnn/stream-z/releases"><img alt="release" src="https://img.shields.io/github/v/release/micsxnn/stream-z?include_prereleases&label=vers%C3%A3o&color=a78bfa"></a>
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/badge/licen%C3%A7a-MIT-38bdf8"></a>
  <a href="#instala%C3%A7%C3%A3o-como-skill"><img alt="agent skill" src="https://img.shields.io/badge/agente-skill-f0abfc"></a>
</p>

**stream-z** é uma skill de agente que transforma o trabalho do assistente em uma **transmissão ao vivo**: todo texto que o agente fala é publicado em um site próprio **antes** de aparecer no chat — incluindo as narrativas intermediárias entre tool calls. Se a plataforma de chat travar, a transmissão continua. Cada turno termina com um marcador «F I M» desenhado no próprio feed.

Funciona com qualquer agente que execute comandos (shell + Python 3). Zero infraestrutura: o banco do feed é um **gist secreto do GitHub**, o site é estático e o push é um script de 100 linhas.

## Como funciona

```
 sandbox do agente                GitHub (gist SECRETO)                site do viewer
 ─────────────────                ─────────────────────                ──────────────
 mirror_push.py ── PATCH ────▶  feed.json  ◀── GET autenticado ───  /api/feed (proxy)
 (cada fala, verbatim,          {items:[{t,k,x}]}                    │ cache: no-store
  ANTES do chat)                                                      ▼
                                                      viewer estático (poll 2,5 s)
```

1. O agente empurra cada fala para o gist com `scripts/mirror_push.py` — **sempre antes de exibir no chat**.
2. O viewer consulta o feed a cada 2,5 s, sem cache, e agrupa falas consecutivas do mesmo emissor.
3. Um **proxy serverless** (`/api/feed`) lê o gist autenticado: o CDN do gist nunca serve versão velha e o **token nunca chega ao navegador**.
4. O feed se auto-trunca (400 itens / 400 KB) — pode transmitir por dias sem manutenção.

## Instalação como skill

> **Regra de instalação — sempre do zero.** Para instalar ou reinstalar a skill,
> clone a pasta inteira novamente (ou baixe o zip da
> [última release](https://github.com/micsxnn/stream-z/releases)) e **substitua a
> pasta anterior por completo**. Nunca atualize por diff, merge ou cópia parcial:
> arquivos podem ter mudado de lugar, sido renomeados ou removidos.

```bash
git clone --depth 1 https://github.com/micsxnn/stream-z <pasta-de-skills>/stream-z
```

Requisitos: Python 3.8+ e um **token GitHub com escopo `gist`** (o agente orienta a criação na primeira montagem).

O que o agente faz com a skill:

- **Operar** (uso diário): transmitir cada fala antes do chat e o «fim» ao encerrar cada turno.
- **Montar do zero**: gist + viewer + proxy, no preview da plataforma ou na Vercel (link fixo).
- **Recuperar**: feed parou de atualizar → diagnóstico e re-conexão guiados.

## Versão e atualizações

- A versão instalada está em [`VERSION`](VERSION) e o histórico em [Releases](https://github.com/micsxnn/stream-z/releases).
- **Checagem automática**: ao carregar a skill, o agente roda
  `python3 <caminho-da-skill>/scripts/check_update.py` — sem ruído, sem interromper.
  Se existir release mais nova que o `VERSION` local, o agente **reinstala a skill do
  zero imediatamente** (apaga a pasta, re-clona, relê o `SKILL.md`) e só informa o
  usuário ao terminar, em uma linha.
- Instalação manual também vale: qualquer dúvida sobre a versão, reinstale do zero.

## Monte o seu stream-z

Dois caminhos documentados, com passo a passo completo (o agente escolhe junto com o usuário):

| Caminho | Onde o viewer mora | Vantagem | Guia |
|---|---|---|---|
| **A** | Vercel (site + proxy) | link fixo, sobrevive a tudo | [`reference/vercel.md`](reference/vercel.md) |
| **B** | preview da plataforma | sobe em minutos | [`reference/preview.md`](reference/preview.md) |

Nos dois casos o banco do feed é o mesmo gist — trocar de caminho **não perde histórico**.

## Protocolo do feed

```json
{"updated": "<ISO-8601>", "items": [{"t": "<ISO>", "k": "<kind>", "x": "<texto>"}]}
```

| `k` | Uso |
|---|---|
| `agent` | qualquer fala do agente que aparecerá no chat (narrativas incluídas) |
| `status` | estados do trabalho ("deployando…", "pronto") |
| `tool` | avisos de ferramenta |
| `user` | reservado (por padrão **nada do usuário é transmitido** — privacidade) |
| `fim` | marcador de fim de turno — desenha o «F I M» no viewer |

## Estrutura

| Caminho | Papel |
|---|---|
| `SKILL.md` | a skill: regra de ouro, operação, configuração, segurança, troubleshooting |
| `VERSION` | versão instalada (comparada com a última release a cada carregamento) |
| `index.html` + `api/feed.js` | viewer + proxy em produção (deploy de referência) |
| `assets/viewer.html`, `assets/feed.js` | templates para montagens novas (copiar, não reimagine) |
| `assets/banner.svg` | identidade visual da skill (banner animado) |
| `reference/vercel.md`, `reference/preview.md` | guias dos caminhos A e B |
| `scripts/mirror_push.py` | transmissão: `--kind agent --text "…"`, `--kind fim --text "fim"` |
| `scripts/create_gist.py` | cria o gist do feed e grava `.secrets/mirror.json` |
| `scripts/check_update.py` | checa a última release contra o `VERSION` local |
| `evals/evals.json` | casos de teste da skill |

## Scripts

```bash
# transmitir uma fala (sempre ANTES de exibir no chat)
GH_TOKEN=ghp_... python3 scripts/mirror_push.py --kind agent --text "fala exata"

# fim de turno
GH_TOKEN=ghp_... python3 scripts/mirror_push.py --kind fim --text "fim"

# checar se há versão nova da skill (exit 0 = em dia, 2 = atualize do zero)
python3 scripts/check_update.py
```

Identificação do gist (nesta ordem): `--gist <id>` → variável `GIST_ID` → `.secrets/mirror.json`.

## Segurança

- Tokens vivem em `.secrets/` (pasta `700`, arquivos `600`), **fora de qualquer git**, e nas env vars do provedor de hospedagem.
- O gist é **secreto**: quem não tem o token não lê; a única porta pública é o proxy `/api/feed`, que só expõe o feed.
- O token nunca é embarcado em código ou template — o proxy lê de variável de ambiente.
- Escopo mínimo: o token do feed precisa só de `gist`.

## FAQ

**O feed quebra se o gist crescer muito?** Não — o push trunca sozinho em 400 itens / 400 KB.

**Trocar o viewer de lugar perde histórico?** Não — o estado vive no gist.

**Posso transmitir também o que o usuário escreve?** O padrão é não. O kind `user` existe, mas transmitir o usuário é decisão explícita dele.

**A transmissão fica lenta?** O viewer faz poll a cada 2,5 s; o proxy responde direto da API do GitHub sem cache.

## Licença

[MIT](LICENSE) © micsxnn
