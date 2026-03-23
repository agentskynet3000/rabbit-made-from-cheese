# Rabbit Made From Cheese

A growing collection of AI-generated images depicting a rabbit made from cheese, placed in increasingly absurd settings.

## Website

A minimalist mosaic grid. Images shuffle on every load. Click any image to view fullscreen.

## Generating New Images

Requires a running [AUTOMATIC1111 Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) at `http://127.0.0.1:7860` with the `juggernautXL_version6Rundiffusion` model loaded.

```bash
python generate-rabbit.py
```

Each run picks a random setting from ~75 options, generates a 1024×1024 image, saves it to `images/`, updates `index.html`, and pushes to GitHub.
