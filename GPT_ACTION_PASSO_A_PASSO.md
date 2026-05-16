# Configurar Action no GPT ClippIA

## 1. Abrir editor do GPT

Abra seu GPT:
https://chatgpt.com/g/g-6a07ca94c5888191a5d04ebec761be9d-clippia-econoroeste

Clique em Editar GPT.

## 2. Criar Action

Vá em:
Configure > Actions > Create new action

## 3. Authentication

Escolha:
API Key

Auth Type:
Bearer

Cole a mesma chave que você colocou na Vercel em:

CLIPPIA_ACTION_KEY

## 4. Schema

Abra o arquivo:

openapi-clippia-action.yaml

Antes de colar, troque:

https://SEU-PROJETO-VERCEL.vercel.app

pelo link real da Vercel.

Depois cole o schema no GPT.

## 5. Instrução extra do GPT

Adicione nas instruções do GPT:

Depois de gerar qualquer relatório de clipagem completo, pergunte ao usuário se deve salvar no ClippIA. Se o usuário disser para salvar, use a Action `salvarClipagemNoClippIA`.

Quando salvar, envie:
- titulo
- periodo
- risco
- categoria
- resumo_executivo
- relatorio
- texto_postagem
- recomendacao
- fontes
- imagens
- noticias

Nunca salve relatório vazio.
Nunca invente fonte.
