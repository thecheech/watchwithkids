module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  let body = req.body;
  if (typeof body === "string") {
    try {
      body = JSON.parse(body);
    } catch {
      return res.status(400).json({ error: "Invalid JSON" });
    }
  }
  if (!body || typeof body !== "object") {
    return res.status(400).json({ error: "Missing body" });
  }

  const report = {
    show: String(body.show || "").slice(0, 80),
    show_id: body.show_id ? String(body.show_id).slice(0, 40) : null,
    code: String(body.code || "").slice(0, 24),
    season: String(body.season || "").slice(0, 12),
    episode: String(body.episode || "").slice(0, 12),
    title: String(body.title || "").slice(0, 160),
    overall: Number(body.overall) || null,
    reason: String(body.reason || "").slice(0, 40),
    reason_label: String(body.reason_label || "").slice(0, 80),
    details: String(body.details || "").slice(0, 600),
    page: String(body.page || "").slice(0, 300),
    at: String(body.at || new Date().toISOString()).slice(0, 40),
  };

  console.log("[report]", JSON.stringify(report));

  const key = process.env.RESEND_API_KEY;
  const to = process.env.REPORT_TO_EMAIL || "kobykarp@gmail.com";
  if (key) {
    try {
      await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${key}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from: process.env.REPORT_FROM_EMAIL || "Watch With The Kids <onboarding@resend.dev>",
          to: [to],
          subject: `Report: ${report.show} ${report.code} — ${report.reason_label}`,
          text: [
            `${report.show} · ${report.code}`,
            `${report.title}`,
            `Overall shown: ${report.overall}`,
            `Reason: ${report.reason_label}`,
            report.details ? `Details: ${report.details}` : null,
            `Page: ${report.page}`,
            `At: ${report.at}`,
          ]
            .filter(Boolean)
            .join("\n"),
        }),
      });
    } catch (err) {
      console.error("[report] email failed", err);
    }
  }

  return res.status(200).json({ ok: true });
};
