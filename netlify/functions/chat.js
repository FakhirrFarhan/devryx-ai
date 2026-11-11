// Devryx AI — chat function (multi-provider: Gemini -> Groq -> OpenRouter)
// POST /.netlify/functions/chat  { messages: [...], memory: {...} }  ->  { reply } | { error }
// Contract matches the Devryx AI frontend exactly. All providers are OpenAI-compatible.

const BASE_PROMPT =
  "You are Devryx, a warm and genuinely helpful AI companion. Talk like a thoughtful friend: " +
  "natural, conversational, and personable — never stiff or robotic. Answer clearly and concisely. " +
  "Use markdown formatting (headings, lists, code blocks) when it helps readability. " +
  "For code questions, give working code with brief explanations. Be honest about what you don't know. " +
  "Capabilities the app provides automatically (no need to ask the user to enable anything): " +
  "image generation when the user asks for a picture, an interactive map card with weather and directions " +
  "when the user asks about a place or their location, live-location sharing from the map-pin button, " +
  "and short AI video clips when the user asks for a video (handled automatically by the app). " +
  "Follow-up suggestions: at the end of every substantive reply, add one final line with exactly 3 short " +
  "follow-up questions the user might ask next, in this exact format: " +
  "|||first question|||second question|||third question " +
  "Rules: only add them when they genuinely make sense (skip for greetings, errors, apologies, or very " +
  "short answers); keep each under 8 words; never use ||| anywhere else in your reply; keep them plain " +
  "text with no markdown.";

const json = (statusCode, obj) => ({
  statusCode,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(obj),
});

const hasVisionContent = (messages) =>
  messages.some(
    (m) =>
      Array.isArray(m && m.content) &&
      m.content.some((p) => p && p.type === "image_url")
  );

const extractText = (message) => {
  if (!message) return "";
  const c = message.content;
  if (typeof c === "string") return c;
  if (Array.isArray(c))
    return c
      .map((p) => (p && p.type === "text" ? p.text : ""))
      .join("")
      .trim();
  return "";
};

// Providers are tried in order. Each is OpenAI-compatible; keys come from env.
function buildProviders(env, vision) {
  const providers = [];
  if (env.GEMINI_API_KEY)
    providers.push({
      name: "gemini",
      url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
      headers: { "x-goog-api-key": env.GEMINI_API_KEY },
      models: ["gemini-2.5-flash", "gemini-2.0-flash"],
    });
  if (env.GROQ_API_KEY)
    providers.push({
      name: "groq",
      url: "https://api.groq.com/openai/v1/chat/completions",
      headers: { Authorization: "Bearer " + env.GROQ_API_KEY },
      models: vision
        ? []
        : ["openai/gpt-oss-20b", "qwen/qwen3.8-27b"],
    });
  if (env.OPENROUTER_API_KEY)
    providers.push({
      name: "openrouter",
      url: "https://openrouter.ai/api/v1/chat/completions",
      headers: {
        Authorization: "Bearer " + env.OPENROUTER_API_KEY,
        "HTTP-Referer": "https://devryxai.netlify.app",
        "X-Title": "Devryx AI",
      },
      models: vision
        ? ["qwen/qwen3.8-27b:free", "google/gemma-4-31b-it:free"]
        : [
            "qwen/qwen3.8-27b:free",
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
          ],
    });
  return providers;
}

async function tryOnce(provider, model, systemPrompt, messages, ms) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const res = await fetch(provider.url, {
      method: "POST",
      signal: ctrl.signal,
      headers: { "Content-Type": "application/json", ...provider.headers },
      body: JSON.stringify({
        model,
        messages: [{ role: "system", content: systemPrompt }, ...messages],
        temperature: 0.7,
        max_tokens: 2048,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401 || res.status === 403)
      return { fatal: "auth", detail: data };
    if (res.status === 429) return { retry: true, reason: "rate-limit" };
    if (!res.ok) return { retry: true, reason: `upstream-${res.status}` };
    const text = extractText(
      data.choices && data.choices[0] && data.choices[0].message
    );
    if (!text) return { retry: true, reason: "empty-reply" };
    return { ok: true, text };
  } catch (e) {
    return { retry: true, reason: e.name === "AbortError" ? "timeout" : "network" };
  } finally {
    clearTimeout(t);
  }
}

exports.handler = async (event) => {
  if (event.httpMethod !== "POST")
    return json(405, { error: "Method Not Allowed" });

  let messages, memory;
  try {
    const body = JSON.parse(event.body || "{}");
    messages = body.messages;
    memory = body.memory || {};
  } catch {
    return json(200, { error: "Invalid JSON body." });
  }
  if (!Array.isArray(messages) || messages.length === 0)
    return json(200, { error: "No messages provided." });

  let systemPrompt = BASE_PROMPT;
  const userName =
    typeof memory.name === "string" ? memory.name.trim().slice(0, 40) : "";
  if (userName)
    systemPrompt +=
      ' The user\'s name is "' +
      userName.replace(/"/g, "") +
      '". ' +
      "Address them by name occasionally and naturally — warmly, never forced.";

  const providers = buildProviders(process.env, hasVisionContent(messages));
  if (!providers.length)
    return json(200, {
      error:
        "No chat provider is configured. Add GEMINI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY in Netlify -> Site configuration -> Environment variables.",
    });

  // Global deadline keeps us safely under Netlify's function timeout.
  const deadline = Date.now() + 24000;
  let lastReason = "unknown";
  for (const provider of providers) {
    for (const model of provider.models) {
      const remaining = deadline - Date.now();
      if (remaining < 3000) break;
      const r = await tryOnce(
        provider,
        model,
        systemPrompt,
        messages,
        Math.min(12000, remaining - 500)
      );
      if (r.ok) return json(200, { reply: r.text });
      if (r.fatal === "auth") {
        lastReason = provider.name + ": bad API key (skipping provider)";
        break; // try the next provider
      }
      lastReason = `${provider.name}/${model}: ${r.reason}`;
    }
  }
  return json(200, {
    error:
      "All chat providers are busy or rate-limited right now (" +
      lastReason +
      "). Wait a minute and try again.",
  });
};
