// Devryx AI — image function (free tier chain)
// POST /.netlify/functions/image  { prompt }  ->  { image, mimeType, text } | { error }
// Contract matches the Devryx AI frontend exactly (base64 image payload).
//
// History: the old primary (HF "nscale" provider serving FLUX.1-schnell) was
// deprecated by Hugging Face and now errors on every call; hf-inference
// returns 410 for the same model. Current chain:
//   1. Pollinations.ai server-side fetch (free, no key). Their servers have
//      blocked datacenter IPs before (402), so this tier may fail from
//      Netlify egress — the browser frontend also calls Pollinations
//      directly as its own primary, which covers residential users.
//   2. The same image function on the Spectra deployment
//      (spectrabydevryx.netlify.app) as a relay: Netlify function egress
//      IPs differ per site, and Pollinations accepts Spectra's pool while
//      rate-limiting this site's (verified 2026-11-11: Devryx direct =
//      402/503, Spectra relay = real images).
//   3. HF router via the fal-ai provider (FLUX.1-schnell). Works only when
//      the HF account has Inference Provider credits or PRO; returns 402
//      otherwise, which is treated as a normal tier failure.
// Either tier returning bytes wins; if both fail, the frontend falls back
// to its browser-side Pollinations call and then an error message.

const json = (statusCode, obj) => ({
  statusCode,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(obj),
});

async function fetchWithTimeout(url, opts, ms) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(url, { ...opts, signal: ctrl.signal });
  } finally {
    clearTimeout(t);
  }
}

async function tryPollinations(prompt, ms) {
  const seed = Math.floor(Math.random() * 1000000000);
  const url =
    "https://image.pollinations.ai/prompt/" +
    encodeURIComponent(prompt) +
    "?model=flux&width=1024&height=1024&seed=" +
    seed +
    "&nologo=true";
  try {
    const res = await fetchWithTimeout(url, { method: "GET" }, ms);
    if (!res.ok) return { fatal: "http-" + res.status };
    const ct = (res.headers.get("content-type") || "").split(";")[0];
    if (!ct.startsWith("image/")) return { fatal: "not-image:" + ct };
    const buf = Buffer.from(await res.arrayBuffer());
    if (!buf.length) return { fatal: "empty" };
    return { ok: true, b64: buf.toString("base64"), mime: ct };
  } catch (e) {
    return { fatal: e.name === "AbortError" ? "timeout" : "network" };
  }
}

async function trySpectraRelay(prompt, ms) {
  try {
    const res = await fetchWithTimeout(
      "https://spectrabydevryx.netlify.app/.netlify/functions/image",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      },
      ms
    );
    const data = await res.json().catch(() => ({}));
    if (data && data.image)
      return { ok: true, b64: data.image, mime: data.mimeType || "image/jpeg" };
    return { fatal: (data && data.detail) || "relay-error" };
  } catch (e) {
    return { fatal: e.name === "AbortError" ? "timeout" : "network" };
  }
}

async function tryFalAi(apiKey, prompt, ms) {
  try {
    const res = await fetchWithTimeout(
      "https://router.huggingface.co/fal-ai/v1/images/generations",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: "fal-ai/flux/schnell",
          prompt,
        }),
      },
      ms
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = JSON.stringify(data).slice(0, 200);
      if (res.status === 402) return { fatal: "no-credits", detail };
      if (res.status === 401 || res.status === 403)
        return { fatal: "auth", detail };
      if (res.status === 429) return { fatal: "ratelimit", detail };
      return { fatal: "upstream", detail };
    }
    const item = data.data && data.data[0];
    if (item && item.b64_json)
      return { ok: true, b64: item.b64_json, mime: "image/png" };
    if (item && item.url) {
      const r2 = await fetchWithTimeout(item.url, { method: "GET" }, ms);
      if (!r2.ok) return { fatal: "empty" };
      const buf = Buffer.from(await r2.arrayBuffer());
      const ct = (r2.headers.get("content-type") || "image/png").split(";")[0];
      return { ok: true, b64: buf.toString("base64"), mime: ct };
    }
    return { fatal: "empty" };
  } catch (e) {
    return { fatal: e.name === "AbortError" ? "timeout" : "network" };
  }
}

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
  prompt = prompt.trim().slice(0, 1500);

  // Tier 1: Pollinations server-side (free, no key).
  let r = await tryPollinations(prompt, 8000);
  if (r.ok) return json(200, { image: r.b64, mimeType: r.mime, text: "" });
  const tiers = ["pollinations=" + (r.fatal || "unknown")];

  // Tier 2: Spectra relay (different Netlify egress pool).
  r = await trySpectraRelay(prompt, 12000);
  if (r.ok) return json(200, { image: r.b64, mimeType: r.mime, text: "" });
  tiers.push("spectra-relay=" + (r.fatal || "unknown"));

  // Tier 3: HF via fal-ai (only if a key is configured).
  const apiKey = process.env.HF_API_KEY;
  if (apiKey) {
    r = await tryFalAi(apiKey, prompt, 5000);
    if (r.ok) return json(200, { image: r.b64, mimeType: r.mime, text: "" });
    tiers.push("fal-ai=" + (r.fatal || "unknown"));
  } else {
    tiers.push("fal-ai=skipped:no-key");
  }

  return json(200, {
    error: "Image generation failed, please try again in a moment.",
    detail: tiers.join("; "),
  });
};
