// Devryx AI — image function (free tier chain)
// POST /.netlify/functions/image  { prompt }  ->  { image, mimeType, text } | { error }
// Contract matches the Devryx AI frontend exactly (base64 image payload).
//
// Primary: HF Inference Router "nscale" provider (OpenAI-images-compatible)
// with black-forest-labs/FLUX.1-schnell — the only text-to-image model nscale
// serves, and the only reliable free image model available (verified 2026-10-07:
// FLUX.1-dev is "not supported by provider nscale"; legacy hf-inference 410s).
// The browser also carries a client-side Pollinations.ai fallback (its servers
// block Netlify's egress IPs with 402, but residential IPs work fine).

const json = (statusCode, obj) => ({
  statusCode,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(obj),
});

const NSCALE_URL =
  "https://router.huggingface.co/nscale/v1/images/generations";
const PRIMARY_MODEL = "black-forest-labs/FLUX.1-schnell";

async function tryNscale(apiKey, prompt, ms) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const res = await fetch(NSCALE_URL, {
      method: "POST",
      signal: ctrl.signal,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: PRIMARY_MODEL,
        prompt,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401 || res.status === 403) return { fatal: "auth" };
    if (res.status === 429) return { fatal: "ratelimit" };
    if (!res.ok) {
      const detail = JSON.stringify(data).slice(0, 300);
      if (/loading|warming/i.test(detail)) return { fatal: "loading" };
      return { fatal: "upstream", detail };
    }
    const item = data.data && data.data[0];
    if (item && item.b64_json)
      return { ok: true, b64: item.b64_json, mime: "image/png" };
    if (item && item.url) {
      const r2 = await fetch(item.url);
      if (!r2.ok) return { fatal: "empty" };
      const buf = Buffer.from(await r2.arrayBuffer());
      const ct = (r2.headers.get("content-type") || "image/png").split(";")[0];
      return { ok: true, b64: buf.toString("base64"), mime: ct };
    }
    return { fatal: "empty" };
  } catch (e) {
    return { fatal: e.name === "AbortError" ? "timeout" : "network" };
  } finally {
    clearTimeout(t);
  }
}

const TRANSIENT = new Set(["ratelimit", "loading", "timeout", "network"]);

exports.handler = async (event) => {
  if (event.httpMethod !== "POST")
    return json(405, { error: "Method Not Allowed" });

  let prompt;
  try {
    prompt = (JSON.parse(event.body || "{}") || {}).prompt;
  } catch {
    return json(200, { error: "Invalid JSON body." });
  }
  if (typeof prompt !== "string" || !prompt.trim())
    return json(200, { error: "Please describe the image you want." });
  prompt = prompt.trim();

  const apiKey = process.env.HF_API_KEY;
  if (!apiKey) {
    return json(200, {
      error: "Image generation is not configured right now.",
      detail: "primary=skipped:no-key",
    });
  }

  // One retry on transient failures (rate limit / cold model / blip).
  let r = await tryNscale(apiKey, prompt.slice(0, 1500), 25000);
  let fatal = r.fatal + (r.detail ? "|" + r.detail.slice(0, 200) : "");
  if (!r.ok && TRANSIENT.has(r.fatal)) {
    await new Promise((ok) => setTimeout(ok, 3000));
    r = await tryNscale(apiKey, prompt.slice(0, 1500), 25000);
    fatal = r.fatal + (r.detail ? "|" + r.detail.slice(0, 200) : "");
  }
  if (r.ok) return json(200, { image: r.b64, mimeType: r.mime, text: "" });

  return json(200, {
    error:
      "Image generation failed, please try again in a moment.",
    detail: `primary=${fatal || "unknown"}`,
  });
};
