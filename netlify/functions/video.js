// Devryx — premium video broker (LTX-2 via Hugging Face ZeroGPU)
// POST /.netlify/functions/video
//   { prompt, firstFrame?, lastFrame?, camera?, width?, height?, enhance? }
//   firstFrame/lastFrame: base64 data URLs (jpeg/png), optional.
//   ->  { event_id, base, endpoint } | { error }
//
// Why a broker: the LTX-2 spaces with Flow-class quality are ZeroGPU
// spaces. Anonymous calls are rejected ("ZeroGPU runs limit"), but calls
// carrying the site's own HF token are attributed to the account's daily
// free ZeroGPU quota. The token must never ship in public frontend code,
// so the browser asks this function to START the job; the function returns
// the event_id and the browser then streams progress/results directly
// from the Space (event streams are addressed by event_id only).
// When the daily free quota is used up, the Space returns a quota error
// on the stream and the frontend falls back to the fast LTX engine.
//
// Callers: the Devryx AI app itself (same origin) and ReelForge, the
// Devryx Labs video studio (cross-origin, allowlisted below).

const ALLOWED_ORIGINS = [
  "https://devryxai.netlify.app",
  "https://reelforge.netlify.app",
  "https://reelforgebydevryx.netlify.app",
];

const SPACE_BASE = "https://alexnasa-ltx-2-turbo.hf.space";
const ENDPOINT = "generate_video";
const CAMERA_OPTIONS = [
  "No LoRA", "Static", "Detailer", "Zoom In", "Zoom Out",
  "Slide Left", "Slide Right", "Slide Down", "Slide Up",
];

function corsHeaders(event) {
  const origin = (event.headers || {}).origin || "";
  const h = { "Content-Type": "application/json", Vary: "Origin" };
  if (ALLOWED_ORIGINS.includes(origin))
    h["Access-Control-Allow-Origin"] = origin;
  return h;
}

const json = (event, statusCode, obj) => ({
  statusCode,
  headers: corsHeaders(event),
  body: JSON.stringify(obj),
});

async function uploadFrame(apiKey, dataUrl) {
  // data:image/jpeg;base64,....  ->  gradio temp file path on the Space
  const m = /^data:(image\/(?:jpeg|png|webp));base64,(.+)$/.exec(dataUrl || "");
  if (!m) return null;
  const buf = Buffer.from(m[2], "base64");
  if (buf.length < 100 || buf.length > 4000000) return null;
  const ext = m[1].split("/")[1].replace("jpeg", "jpg");
  const form = new FormData();
  form.append(
    "files",
    new Blob([buf], { type: m[1] }),
    `frame.${ext}`
  );
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 20000);
  try {
    const res = await fetch(`${SPACE_BASE}/gradio_api/upload`, {
      method: "POST",
      signal: ctrl.signal,
      headers: { Authorization: `Bearer ${apiKey}` },
      body: form,
    });
    const j = await res.json().catch(() => null);
    const path = Array.isArray(j) ? j[0] : null;
    if (!res.ok || !path) return null;
    return {
      path,
      url: `${SPACE_BASE}/gradio_api/file=${path}`,
      orig_name: `frame.${ext}`,
      mime_type: m[1],
    };
  } catch {
    return null;
  } finally {
    clearTimeout(t);
  }
}

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    const h = corsHeaders(event);
    h["Access-Control-Allow-Methods"] = "POST, OPTIONS";
    h["Access-Control-Allow-Headers"] = "Content-Type";
    h["Access-Control-Max-Age"] = "86400";
    return { statusCode: 204, headers: h, body: "" };
  }
  if (event.httpMethod !== "POST")
    return json(event, 405, { error: "Method Not Allowed" });
  if (event.body && event.body.length > 9000000)
    return json(event, 200, { error: "Request too large." });

  let body;
  try {
    body = JSON.parse(event.body || "{}") || {};
  } catch {
    return json(event, 200, { error: "Invalid JSON body." });
  }
  let prompt = body.prompt;
  if (typeof prompt !== "string" || prompt.trim().length < 3)
    return json(event, 200, { error: "Please describe the video you want." });
  prompt = prompt.trim().slice(0, 600);

  const apiKey = process.env.HF_API_KEY;
  if (!apiKey)
    return json(event, 200, { error: "Premium video is not configured." });

  // Optional frames (image-to-video / first+last frame control)
  let firstFrame = null;
  let lastFrame = null;
  if (body.firstFrame) {
    firstFrame = await uploadFrame(apiKey, body.firstFrame);
    if (!firstFrame)
      return json(event, 200, { error: "Could not upload the start frame." });
  }
  if (body.lastFrame) {
    lastFrame = await uploadFrame(apiKey, body.lastFrame);
    if (!lastFrame)
      return json(event, 200, { error: "Could not upload the end frame." });
  }

  const camera = CAMERA_OPTIONS.includes(body.camera) ? body.camera : "No LoRA";
  const clampDim = (v, dflt) => {
    const n = parseInt(v, 10);
    return Number.isFinite(n) ? Math.min(1024, Math.max(256, n)) : dflt;
  };
  const height = clampDim(body.height, 512);
  const width = clampDim(body.width, 768);
  const mode = firstFrame || lastFrame ? "Image-to-Video" : "Text-to-Video";

  const seed = Math.floor(Math.random() * 100000);
  const data = [
    firstFrame, // First Frame (optional)
    lastFrame, // Last Frame (optional)
    prompt,
    null, // Reference Video
    mode,
    body.enhance === false ? false : true, // Enhance Prompt
    seed,
    true, // Randomize Seed
    height,
    width,
    camera,
    null, // Audio (optional)
  ];

  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 20000);
  try {
    const res = await fetch(`${SPACE_BASE}/gradio_api/call/${ENDPOINT}`, {
      method: "POST",
      signal: ctrl.signal,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({ data }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.event_id) {
      const detail = JSON.stringify(j).slice(0, 200);
      return json(event, 200, {
        error: "Premium video engine is busy right now.",
        detail,
      });
    }
    return json(event, 200, {
      event_id: j.event_id,
      base: SPACE_BASE,
      endpoint: ENDPOINT,
    });
  } catch (e) {
    return json(event, 200, {
      error:
        e.name === "AbortError"
          ? "Premium video engine took too long to respond."
          : "Premium video engine unreachable.",
    });
  } finally {
    clearTimeout(t);
  }
};
