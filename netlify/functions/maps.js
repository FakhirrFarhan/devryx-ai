// Devryx AI — maps/location/weather function (all free, no API keys)
// POST /.netlify/functions/maps
//   { action:"geocode", query }      -> { lat, lon, displayName } | { error }
//   { action:"reverse", lat, lon }   -> { displayName } | { error }
//   { action:"weather", lat, lon }   -> { tempC, humidity, windKph, description, code } | { error }
// Backends: OpenStreetMap Nominatim (geocoding), Open-Meteo (weather).

const UA = "DevryxAI/1.0 (https://devryxai.netlify.app)";

const json = (statusCode, obj) => ({
  statusCode,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(obj),
});

const WEATHER_DESC = {
  0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
  45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
  56: "Freezing drizzle", 57: "Freezing drizzle", 61: "Light rain", 63: "Rain",
  65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain", 71: "Light snow",
  73: "Snow", 75: "Heavy snow", 77: "Snow grains", 80: "Light showers",
  81: "Showers", 82: "Violent showers", 85: "Light snow showers", 86: "Snow showers",
  95: "Thunderstorm", 96: "Storm with hail", 99: "Storm with hail",
};

async function geocode(query) {
  const url =
    "https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" +
    encodeURIComponent(query);
  const res = await fetch(url, { headers: { "User-Agent": UA } });
  if (!res.ok) return { error: "Geocoding service unavailable." };
  const arr = await res.json();
  if (!arr || !arr[0]) return { error: "NOT_FOUND" };
  return {
    lat: parseFloat(arr[0].lat),
    lon: parseFloat(arr[0].lon),
    displayName: arr[0].display_name,
  };
}

async function reverse(lat, lon) {
  const url =
    `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`;
  const res = await fetch(url, { headers: { "User-Agent": UA } });
  if (!res.ok) return { error: "Reverse-geocoding unavailable." };
  const d = await res.json();
  return { displayName: d.display_name || "Unknown location" };
}

async function weather(lat, lon) {
  const url =
    `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
    `&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&temperature_unit=celsius`;
  const res = await fetch(url);
  if (!res.ok) return { error: "Weather service unavailable." };
  const d = await res.json();
  const c = d.current || {};
  return {
    tempC: c.temperature_2m,
    humidity: c.relative_humidity_2m,
    windKph: c.wind_speed_10m,
    code: c.weather_code,
    description: WEATHER_DESC[c.weather_code] || "—",
  };
}

exports.handler = async (event) => {
  if (event.httpMethod !== "POST")
    return json(405, { error: "Method Not Allowed" });
  let body;
  try {
    body = JSON.parse(event.body || "{}");
  } catch {
    return json(200, { error: "Invalid JSON body." });
  }
  try {
    if (body.action === "geocode") {
      if (!body.query) return json(200, { error: "Missing query." });
      return json(200, await geocode(String(body.query).slice(0, 200)));
    }
    if (body.action === "reverse") {
      return json(200, await reverse(parseFloat(body.lat), parseFloat(body.lon)));
    }
    if (body.action === "weather") {
      return json(200, await weather(parseFloat(body.lat), parseFloat(body.lon)));
    }
    return json(200, { error: "Unknown action." });
  } catch (e) {
    return json(200, { error: "Location service error, try again." });
  }
};
