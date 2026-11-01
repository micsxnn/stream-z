// stream-z :: /api/feed — proxy de leitura do feed (sempre fresco)
// Lê o gist via API do GitHub autenticada; o token nunca vai ao navegador.
// Configuração por env var: GIST_ID (id do gist do feed) e GH_TOKEN (escopo gist).

module.exports = async (req, res) => {
  const gist = process.env.GIST_ID;
  if (!gist || !process.env.GH_TOKEN) {
    res.status(500).json({ error: "env ausente: configure GIST_ID e GH_TOKEN no provedor de hospedagem" });
    return;
  }
  try {
    const r = await fetch(`https://api.github.com/gists/${gist}`, {
      headers: {
        Authorization: `Bearer ${process.env.GH_TOKEN}`,
        "User-Agent": "stream-z",
        Accept: "application/vnd.github+json",
      },
      cache: "no-store",
    });
    if (!r.ok) {
      res.status(502).json({ error: "upstream " + r.status });
      return;
    }
    const j = await r.json();
    const feed = JSON.parse(j.files["feed.json"].content);
    res.setHeader("Cache-Control", "no-store");
    res.status(200).json(feed);
  } catch (e) {
    res.status(500).json({ error: "falha ao ler feed" });
  }
};
