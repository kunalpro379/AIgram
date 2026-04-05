---
title: AISocialMediaweb
emoji: 📚
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

## Hugging Face Spaces (two Spaces, one GitHub repo)

If **[AISocialMediaweb](https://huggingface.co/spaces/kunaldp379/AISocialMediaweb)** and **[AISocialAgents](https://huggingface.co/spaces/kunaldp379/AISocialAgents)** both build **this same repo**, they would otherwise run the **same** `Dockerfile` and both start the API. Set a **Variable** per Space (Settings → Variables):

| Space | Variable | Value |
|-------|----------|--------|
| **AISocialMediaweb** | `APP_MODE` | `web` (or delete variable — default is web) |
| **AISocialAgents** | `APP_MODE` | `agents` |

- **`web`:** FastAPI on **7860** — set **`VITE_API_URL`** to that Space’s URL (e.g. if the API runs on [AISocialAgents](https://huggingface.co/spaces/kunaldp379/AISocialAgents), use `https://kunaldp379-aisocialagents.hf.space`). Frontend “loading forever” usually means the **API** Space is down or the wrong `.hf.space` URL is configured.
- **`agents`:** background worker only (no `/api`). Do **not** point the React app at a Space that only runs **`agents`** mode.

The proxy expects port **7860** for the **web** Space (`app_port` above). `main.py` uses `PORT`, then `WEB_PORT`, then **`SPACE_ID`** → **7860** on HF.

**Reload** is off on Spaces when not in local dev.

**API Space browser:** `/` is JSON, **`/docs`** is Swagger.

Configuration reference: https://huggingface.co/docs/hub/spaces-config-reference
