# ClippIA Econoroeste — Realtime Database + Vercel + GPT Action

Este pacote faz a opção 3 usando:

- GitHub para guardar os arquivos
- GitHub Actions para coletar notícias
- Vercel para criar a API
- Firebase Realtime Database como banco JSON
- GPT personalizado com Action para salvar automaticamente no banco

## Fluxo final

1. O painel coleta notícias.
2. Você clica em "Copiar e abrir GPT".
3. O GPT analisa, pesquisa e gera o relatório.
4. O GPT chama a Action `salvarClipagemNoClippIA`.
5. A Vercel recebe a chamada.
6. A Vercel salva no Firebase Realtime Database em `/clipagens`.
7. O painel mostra a clipagem salva.

## Arquivos principais

- `index.html`: painel do ClippIA
- `firebase-config.js`: configuração do Firebase Web
- `api/salvar-clipagem.js`: API Vercel chamada pelo GPT Action
- `api/health.js`: teste da API
- `openapi-clippia-action.yaml`: schema para colar no GPT
- `scripts/coletar_noticias.py`: coletor de notícias
- `.github/workflows/coletar-noticias.yml`: automação do GitHub Actions

## Banco usado

Firebase Realtime Database.

A estrutura ficará assim:

```json
{
  "clipagens": {
    "-ID_GERADO": {
      "titulo": "...",
      "risco": "medio",
      "relatorio": "...",
      "texto_postagem": "...",
      "fontes": [],
      "imagens": [],
      "criado_em": "..."
    }
  },
  "ultima_clipagem": {
    "id": "-ID_GERADO",
    "titulo": "...",
    "risco": "medio"
  },
  "logs": {
    "actions": {}
  }
}
```

## Variáveis da Vercel

Crie estas variáveis em Project Settings > Environment Variables:

- `CLIPPIA_ACTION_KEY`
- `FIREBASE_DATABASE_URL`
- `FIREBASE_SERVICE_ACCOUNT_JSON`

Opcional:

- `ALLOWED_ORIGIN`

## Regras do Realtime Database para o painel

Comece com estas regras:

```json
{
  "rules": {
    "clipagens": {
      ".read": "auth != null",
      ".write": "auth != null"
    },
    "ultima_clipagem": {
      ".read": "auth != null",
      ".write": false
    },
    "logs": {
      ".read": false,
      ".write": false
    }
  }
}
```

A Vercel usa Firebase Admin SDK, então consegue salvar mesmo com regra de escrita bloqueada para cliente, desde que esteja usando Service Account.
