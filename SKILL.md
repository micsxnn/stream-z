---
name: stream-z
description: Stream-z — transmite ao vivo TODAS as falas do agente (incluindo narrativas intermediárias entre tool calls) para o site stream-z-ofc.vercel.app, ANTES de aparecerem no chat, com marcador «fim» no fim de cada turno. Use SEMPRE que o usuário pedir para trabalhar "com o stream-z ligado", "no stream-z", "me mostrando ao vivo", "streama pro site", "quero ver você trabalhando" ou qualquer acompanhamento em tempo real; também use para montar o ambiente do zero (gist + viewer + push) ou para reconectar/recuperar um stream-z que parou de atualizar. Não serve para tarefas rápidas em que ninguém está assistindo — aí o uso é opcional.
---

# stream-z — transmissão ao vivo

O usuário acompanha seu trabalho em tempo real num site estático que lê um feed JSON.
Você transmite cada fala para o feed ANTES de escrevê-la no chat — mesmo quando a
plataforma travar, o stream-z continua mostrando o que você está fazendo.

> **Nome oficial: stream-z** (site stream-z-ofc.vercel.app). Apelido antigo «espelho» —
> mesmo serviço; se alguém disser "espelho", é esta skill aqui.

## Instalação (esta skill É este repositório)

```bash
git clone https://github.com/micsxnn/stream-z <pasta-de-skills>/stream-z
```

Pronto: SKILL.md, scripts, assets e evals juntos na pasta clonada. Atualize com
`git -C <pasta-de-skills>/stream-z pull`. Nos exemplos desta skill,
`<caminho-da-skill>` = a pasta do clone (ex.: `/home/z/my-project/skills/stream-z`).

Os arquivos `index.html` e `api/feed.js` na raiz são a cópia em produção
(viewer na Vercel, stream-z-ofc.vercel.app) — mesmo código dos templates em
`assets/`. `scripts/create_gist.py` e `scripts/insert_fim_history.py` são
utilitários de primeira montagem e correção de histórico.

## Arquitetura

```
sandbox (você)                      GitHub (gist SECRETO = banco do feed)
mirror_push.py  ── PATCH ──────▶   feed.json = {"updated","items":[{t,k,x}]}
                                        │ GET autenticado
                                        ▼
                        proxy serverless /api/feed  (o token NUNCA vai ao navegador)
                                        │ no-store, sem cache
                                        ▼
                        viewer estático (poll 2,5 s, agrupa emissores, marca «F I M»)
```

Por que um gist e não um banco? Zero infraestrutura, versionamento de graça e a API
aceita PATCH num único arquivo. Por que um proxy? O CDN do gist cacheia a resposta —
sem o `/api/feed` autenticado o viewer mostra feed velho.

## A REGRA DE OURO — operar vem antes de montar

Se o stream-z já existe (`.secrets/mirror.json` com `gist_id`, ou o usuário informou
o site/token), PULE a configuração e vá direto para "Operação".

1. **Todo texto que você falar no chat vai PRIMEIRO pro stream-z, verbatim, e DEPOIS
   aparece no chat.** Inclui narrativas intermediárias entre tool calls ("vou checar…",
   "agora vou montar…"). Se um turno tem 6 falas, o stream-z recebe as 6.
2. **Ao TERMINAR cada turno**: `--kind fim --text "fim"` — desenha o marcador «F I M»
   que separa os turnos no site.
3. **Mensagens do USUÁRIO nunca vão pro stream-z** (privacidade).
4. Push falhou? Repita. O viewer mostra banner "sem sinal" após 3 polls sem update —
   isso quase sempre significa que VOCÊ parou de transmitir.

### Operação (a cada fala)

```bash
set -a && source /home/z/my-project/.secrets/tokens.env && set +a
python3 <caminho-da-skill>/scripts/mirror_push.py --kind agent --text "<sua fala EXATA>"
```

| kind | quando usar |
|---|---|
| `agent` | qualquer texto seu que aparecerá no chat (narrativas incluídas) |
| `status` | estados do trabalho ("deployando…", "pronto") |
| `tool` | avisos de ferramenta, se quiser marcar |
| `fim` | UMA vez, no fim de cada turno |

O agrupamento de falas consecutivas do mesmo emissor é automático no viewer — o
símbolo «z» não se repete a cada parágrafo. É feature, não bug; não tente "corrigir".

## Configuração (montar do zero)

**PASSO 1 — pergunte ao usuário onde o viewer vai morar** (use exatamente esta pergunta):

> Onde você quer ver o stream-z: **(A) na Vercel** — link fixo, tipo
> `stream-z-ofc.vercel.app`, sobrevive a tudo — **ou (B) no preview da plataforma** —
> mais rápido de subir, mas o link é gigante e muda a cada sessão?

- Resposta **A → leia `reference/vercel.md`** e siga o passo a passo completo
  (inclui orientar o usuário a criar o token Vercel com escopo **Full Account**).
- Resposta **B → leia `reference/preview.md`** e siga o passo a passo completo
  (inclui ENCURTAR o link do preview com is.gd antes de entregá-lo ao usuário).

Pré-requisitos dos dois caminhos (recolha tudo antes de começar):

- **Token GitHub** com escopo `gist` — o usuário cria em github.com → Settings →
  Developer settings → Personal access tokens (clássico) e te manda no chat.
- Os arquivos prontos estão nesta skill: `assets/viewer.html` (o site), `assets/feed.js`
  (o proxy de leitura) e `scripts/mirror_push.py` (a transmissão). **Copie, não
  reimagine** — eles já implementam agrupamento, «F I M», skeleton e truncagem.

## Memória (repo cérebro)

O contexto do projeto vive no repo privado `micsxnn/cerebro`, pasta `stream-z/` —
sandboxes são recicladas; o cérebro, não.

- **Início de sessão com o stream-z**: clone/leia `stream-z/CONTEXTO.md` do cérebro
  ANTES de decidir qualquer coisa — o estado real do projeto está lá, não na sua
  memória da conversa.
- **Fim de turno com progresso**: atualize o CONTEXTO.md (estado, decisões,
  pendências) e commite. Regras do cérebro: pasta do projeto primeiro; segredos
  NUNCA — tokens ficam só na sandbox (`.secrets/`), fornecidos e revogados pelo usuário.

## Segurança

- Tokens morrem em `.secrets/` (pasta 700, arquivos 600), FORA de qualquer git.
- Em toda chamada Bash que usa token: `set -a && source .secrets/tokens.env && set +a`.
- O token NUNCA vai ao navegador — o viewer só conversa com o proxy.
- No fim do projeto, lembre o usuário de REVOGAR os tokens (GitHub e Vercel).

## Troubleshooting

- **Feed velho no site** → o viewer deve ler `/api/feed` (proxy no-store), nunca
  `gist.githubusercontent.com` direto (o CDN do gist cacheia).
- **Feed cresce sem parar** → `mirror_push.py` trunca sozinho (400 itens / 400 KB).
- **401 no push** → token girou/revogou; peça um novo ao usuário e atualize
  `.secrets/tokens.env`.
- **Preview fora do ar** → o preview vive enquanto a sessão vive; suba de novo e
  re-encurte o link — o feed está no gist, nada se perde.
