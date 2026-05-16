# Passo a passo Firebase Realtime Database

## 1. Criar projeto

Acesse:
https://console.firebase.google.com/

Crie o projeto:
clippia-econoroeste

## 2. Criar app Web

Projeto > engrenagem > Configurações do projeto > Geral > Seus apps > Web

Copie o objeto firebaseConfig e cole em `firebase-config.js`.

IMPORTANTE:
O `databaseURL` é obrigatório.

Formato:
```js
databaseURL: "https://SEU-PROJETO-default-rtdb.firebaseio.com"
```

## 3. Ativar Authentication

Build > Authentication > Get started > Sign-in method > Email/Password > Enable.

## 4. Criar Realtime Database

Build > Realtime Database > Create Database.

Escolha uma região e comece em modo bloqueado/locked.

## 5. Regras

Em Realtime Database > Rules, cole:

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

## 6. Criar Service Account para Vercel

Projeto > engrenagem > Configurações do projeto > Contas de serviço.

Clique em:
Gerar nova chave privada.

Vai baixar um JSON.

Copie o conteúdo inteiro do JSON e cole na Vercel como variável:

FIREBASE_SERVICE_ACCOUNT_JSON

Nunca coloque esse JSON no GitHub.
