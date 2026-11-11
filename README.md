# Devryx AI

My own AI web app, live at https://devryxai.netlify.app

I built Devryx AI and I still actively develop it. It is a real product I ship updates to, not a tutorial or template project.

## What it does

- AI chat with a multi provider fallback chain
- AI image generation
- AI video generation
- Maps and location features
- Voice chat
- Themes and a custom interface I designed myself

## How it is built

- Frontend: HTML, CSS and JavaScript in `public/`, with the main app in `public/index.html`
- Backend: Netlify serverless functions in `netlify/functions/`
  - `chat.js` handles AI chat, trying Gemini, then Groq, then OpenRouter
  - `image.js` handles image generation through Hugging Face FLUX
  - `maps.js` handles maps and location requests
- API keys live only as Netlify environment variables, never in this code
- `deploy_site.py` is my deploy script for the site
- The `edit_*.py` scripts are the tooling I used while building out the frontend, themes and video features

## Ownership

Devryx AI is my project and my code. It is the flagship app of Devryx Labs, my own product studio.

Fakhir Farhan
Full stack developer and UI/UX designer, Maryland, USA
Portfolio: https://fakhirfarhan.com
