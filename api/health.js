export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", process.env.ALLOWED_ORIGIN || "*");
  res.status(200).json({
    ok: true,
    name: "ClippIA Econoroeste API",
    database: "Firebase Realtime Database",
    message: "API online. Use POST /api/salvar-clipagem",
    time: new Date().toISOString()
  });
}
