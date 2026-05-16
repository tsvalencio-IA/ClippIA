# ClippIA Econoroeste — passo a passo para quem só copia e cola

Este pacote cria:

1. Um site/painel no GitHub Pages.
2. Um coletor automático de notícias via GitHub Actions.
3. Um arquivo `data/noticias.json` com notícias coletadas.
4. Um painel para copiar o prompt e mandar para o seu GPT.
5. Um local para salvar o relatório gerado pelo GPT.
6. Integração opcional com Firebase.

## Verdade importante

O GPT Plus não funciona como API gratuita automática dentro do GitHub Actions.
Por isso, a versão barata funciona assim:

GitHub Action coleta links e notícias.
O painel mostra as notícias.
Você clica em copiar prompt.
Você cola no GPT personalizado.
O GPT pesquisa, confirma e gera o relatório.
Você cola o relatório no painel.
O painel salva localmente ou no Firebase.

## Arquivos

- `index.html`: painel do sistema.
- `firebase-config.js`: onde você cola a configuração do Firebase.
- `scripts/coletar_noticias.py`: robô gratuito de coleta.
- `.github/workflows/coletar-noticias.yml`: agenda automática no GitHub Actions.
- `data/noticias.json`: banco simples de notícias públicas coletadas.
- `GPT_INSTRUCOES.md`: instruções para colar no criador de GPT.

## Como subir no GitHub pelo celular

1. Crie um repositório chamado `clippia-econoroeste`.
2. Suba todos estes arquivos mantendo as pastas.
3. Vá em Settings > Pages.
4. Em Source, escolha `Deploy from a branch`.
5. Em Branch, escolha `main` e `/root`.
6. Salve.
7. Aguarde o link aparecer.

## Como rodar a coleta manual

1. Entre no repositório no GitHub.
2. Clique em Actions.
3. Clique em `Coletar notícias Econoroeste`.
4. Clique em `Run workflow`.
5. Aguarde terminar.
6. Abra o site de novo.

## Como configurar Firebase

1. Acesse Firebase Console.
2. Crie um projeto.
3. Crie um app Web.
4. Copie o objeto `firebaseConfig`.
5. Abra o arquivo `firebase-config.js` no GitHub.
6. Clique no lápis para editar.
7. Substitua os campos `COLE_AQUI`.
8. Salve.

## Regras do Firestore

Use estas regras para exigir login:

```
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {
    match /clipagens/{docId} {
      allow read, write: if request.auth != null;
    }
  }
}
```

## Auth

No Firebase, ative Authentication > Sign-in method > Email/Password.

Depois, no painel, você cria a conta pelo próprio site.


## Atualização importante: links + imagens

Esta versão também tenta coletar imagens públicas das notícias e das páginas oficiais.

Ela procura imagens em:
- `media:content` e `media:thumbnail` do RSS
- `og:image`
- `twitter:image`
- primeira imagem relevante da página oficial

No painel existem agora:
- imagem dentro do card da notícia
- botão `Ver imagens coletadas`
- imagem enviada no prompt copiado para o GPT
- campo `image_url` dentro do arquivo `data/noticias.json`

### Limite verdadeiro

Nenhum robô barato consegue garantir todas as imagens de toda a internet, porque:
- alguns portais bloqueiam robôs
- algumas imagens carregam por JavaScript
- algumas páginas têm paywall
- redes sociais podem bloquear scraping
- imagens de portais podem ter direito autoral

O sistema coleta o máximo possível de forma pública e barata, mantendo fonte e link original.
Antes de usar imagem em postagem, confirme se ela é oficial, autorizada ou se precisa de crédito.
