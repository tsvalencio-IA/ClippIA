# Firebase — passo a passo do ClippIA

## 1. Criar projeto

1. Acesse https://console.firebase.google.com/
2. Clique em **Add project** ou **Adicionar projeto**.
3. Nome: `clippia-econoroeste`.
4. Google Analytics: pode deixar desativado no começo.
5. Clique em criar.

## 2. Criar aplicativo Web

1. Dentro do projeto, clique na engrenagem > **Project settings**.
2. Em **Your apps**, clique no ícone Web `</>`.
3. Nome do app: `ClippIA Painel`.
4. Não precisa marcar Firebase Hosting agora.
5. Clique em registrar.
6. Copie somente o objeto `firebaseConfig`.

## 3. Colar no GitHub

Abra no GitHub o arquivo:

`firebase-config.js`

Substitua o conteúdo pelos dados reais, mantendo este formato:

```js
window.firebaseConfig = {
  apiKey: "SUA_API_KEY",
  authDomain: "SEU_PROJETO.firebaseapp.com",
  projectId: "SEU_PROJETO",
  storageBucket: "SEU_PROJETO.appspot.com",
  messagingSenderId: "SEU_NUMERO",
  appId: "SEU_APP_ID"
};
```

Salve com **Commit changes**.

## 4. Ativar login por e-mail e senha

1. Firebase Console > **Build** > **Authentication**.
2. Clique em **Get started**.
3. Vá em **Sign-in method**.
4. Ative **Email/Password**.
5. Clique em **Save**.

## 5. Adicionar domínio autorizado

1. Authentication > **Settings**.
2. Abra **Authorized domains**.
3. Adicione seu domínio do GitHub Pages, por exemplo:

`tsvalencio-ia.github.io`

Se usar domínio próprio depois, adicione também.

## 6. Criar Firestore

1. Firebase Console > **Build** > **Firestore Database**.
2. Clique em **Create database**.
3. Escolha **Production mode**.
4. Escolha região. Para Brasil, se aparecer `southamerica-east1`, pode usar. Se não aparecer, escolha uma região estável próxima.
5. Crie.

## 7. Regras do Firestore

Vá em Firestore Database > **Rules** e cole:

```txt
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {
    match /clipagens/{docId} {
      allow read, write: if request.auth != null;
    }
  }
}
```

Clique em **Publish**.

## 8. Testar

1. Abra o site do ClippIA.
2. Digite e-mail e senha.
3. Clique em **Criar conta**.
4. Depois cole uma resposta do GPT e clique em **Salvar clipagem**.
5. No Firebase > Firestore, veja se apareceu a coleção `clipagens`.
