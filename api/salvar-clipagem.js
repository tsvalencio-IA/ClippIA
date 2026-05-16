import { initializeApp, getApps, cert } from "firebase-admin/app";
import { getDatabase } from "firebase-admin/database";

function setCors(res) {
  res.setHeader("Access-Control-Allow-Origin", process.env.ALLOWED_ORIGIN || "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Clippia-Key");
}

function getServiceAccount() {
  const raw = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
  const b64 = process.env.FIREBASE_SERVICE_ACCOUNT_BASE64;

  let parsed;

  if (raw) {
    parsed = JSON.parse(raw);
  } else if (b64) {
    parsed = JSON.parse(Buffer.from(b64, "base64").toString("utf8"));
  } else {
    throw new Error("Configure FIREBASE_SERVICE_ACCOUNT_JSON ou FIREBASE_SERVICE_ACCOUNT_BASE64 na Vercel.");
  }

  if (parsed.private_key) {
    parsed.private_key = parsed.private_key.replace(/\\n/g, "\n");
  }

  return parsed;
}

function getDb() {
  if (!getApps().length) {
    const serviceAccount = getServiceAccount();
    const databaseURL = process.env.FIREBASE_DATABASE_URL;

    if (!databaseURL) {
      throw new Error("Configure FIREBASE_DATABASE_URL na Vercel. Exemplo: https://SEU-PROJETO-default-rtdb.firebaseio.com");
    }

    initializeApp({
      credential: cert(serviceAccount),
      databaseURL
    });
  }

  return getDatabase();
}

function getKey(req) {
  const auth = req.headers.authorization || "";
  const xKey = req.headers["x-clippia-key"] || "";

  if (auth.toLowerCase().startsWith("bearer ")) {
    return auth.slice(7).trim();
  }

  if (Array.isArray(xKey)) return xKey[0];
  return String(xKey || "").trim();
}

function checkAuth(req) {
  const expected = process.env.CLIPPIA_ACTION_KEY;
  if (!expected) {
    const err = new Error("CLIPPIA_ACTION_KEY não configurada na Vercel.");
    err.status = 500;
    throw err;
  }

  const received = getKey(req);
  if (!received || received !== expected) {
    const err = new Error("Não autorizado. A chave da Action está errada ou ausente.");
    err.status = 401;
    throw err;
  }
}

function textoSeguro(v, limite = 20000) {
  if (v === null || v === undefined) return "";
  return String(v).slice(0, limite);
}

function arraySeguro(v) {
  if (!v) return [];
  if (Array.isArray(v)) return v.slice(0, 50);
  return [v];
}

export default async function handler(req, res) {
  setCors(res);

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  if (req.method === "GET") {
    return res.status(200).json({
      ok: true,
      endpoint: "/api/salvar-clipagem",
      method: "POST",
      database: "Firebase Realtime Database"
    });
  }

  if (req.method !== "POST") {
    return res.status(405).json({ ok: false, error: "Método não permitido. Use POST." });
  }

  try {
    checkAuth(req);

    const body = typeof req.body === "string" ? JSON.parse(req.body) : (req.body || {});
    const db = getDb();

    const agora = new Date().toISOString();

    const clipagem = {
      origem: "gpt_action_clippia",
      status: textoSeguro(body.status || "NOVO", 60),
      titulo: textoSeguro(body.titulo || body.title || "Relatório de clipagem", 500),
      periodo: textoSeguro(body.periodo || "", 200),
      risco: textoSeguro(body.risco || body.risco_imagem || "medio", 60),
      categoria: textoSeguro(body.categoria || "clipagem", 100),
      resumo_executivo: textoSeguro(body.resumo_executivo || ""),
      relatorio: textoSeguro(body.relatorio || body.resposta_completa || body.conteudo || ""),
      texto_postagem: textoSeguro(body.texto_postagem || body.postagem || ""),
      recomendacao: textoSeguro(body.recomendacao || ""),
      fontes: arraySeguro(body.fontes || body.links),
      imagens: arraySeguro(body.imagens),
      noticias: arraySeguro(body.noticias),
      criado_em: agora,
      atualizado_em: agora,
      salvo_por: "GPT Action",
      versao_api: "1.0.0"
    };

    if (!clipagem.relatorio && !clipagem.resumo_executivo && !clipagem.texto_postagem) {
      return res.status(400).json({
        ok: false,
        error: "Envie pelo menos relatorio, resumo_executivo ou texto_postagem."
      });
    }

    const ref = db.ref("clipagens").push();
    await ref.set(clipagem);

    await db.ref("ultima_clipagem").set({
      id: ref.key,
      titulo: clipagem.titulo,
      risco: clipagem.risco,
      criado_em: agora
    });

    await db.ref("logs/actions").push({
      tipo: "salvar_clipagem",
      id: ref.key,
      criado_em: agora
    });

    return res.status(200).json({
      ok: true,
      id: ref.key,
      path: `/clipagens/${ref.key}`,
      message: "Clipagem salva no Firebase Realtime Database."
    });
  } catch (e) {
    const status = e.status || 500;
    return res.status(status).json({
      ok: false,
      error: e.message || String(e)
    });
  }
}
