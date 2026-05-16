# Passo a passo Vercel

## 1. Criar conta

Acesse:
https://vercel.com/

Entre com sua conta GitHub.

## 2. Importar repositório

Clique:
Add New > Project

Escolha o repositório do ClippIA.

Framework Preset:
Other

Deploy.

## 3. Configurar variáveis

Vá em:
Project Settings > Environment Variables

Crie:

### CLIPPIA_ACTION_KEY

Coloque uma senha forte, exemplo:

clippia_uma_chave_grande_123456789

Você vai usar essa mesma chave na Action do GPT.

### FIREBASE_DATABASE_URL

Pegue no Firebase Realtime Database.

Exemplo:

https://clippia-econoroeste-default-rtdb.firebaseio.com

### FIREBASE_SERVICE_ACCOUNT_JSON

Cole o JSON inteiro da chave privada baixada do Firebase.

## 4. Redeploy

Depois de salvar variáveis:

Deployments > três pontinhos no último deploy > Redeploy.

## 5. Testar

Abra:

https://SEU-PROJETO.vercel.app/api/health

Deve aparecer:

ok: true

Depois abra:

https://SEU-PROJETO.vercel.app/api/salvar-clipagem

Deve aparecer informação do endpoint.
