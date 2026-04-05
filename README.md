---
title: AISocialMediaweb
emoji: 📚
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

## Hugging Face Spaces

The server **is running** when you see `Application startup complete.` in the logs.

The proxy expects port **7860** (`app_port` above). The app uses `PORT`, then `WEB_PORT`, then detects Hugging Face via **`SPACE_ID`** and defaults to **7860**; otherwise **8000** for local dev.

**Reload / WatchFiles** is off on Spaces (no reloader spam in logs).

**What you see in the browser:** this Space is the **API** only. Opening the Space URL shows JSON at `/` (and **/docs** for Swagger). The React frontend is normally hosted separately (for example Vercel) with `VITE_API_URL` set to your Space URL (`https://<user>-<space>.hf.space`).

Configuration reference: https://huggingface.co/docs/hub/spaces-config-reference
