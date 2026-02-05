#!/bin/bash
set -e

WEIGHTS_DIR="/app/OmniParser/weights"
MARKER="$WEIGHTS_DIR/.download_complete"

# Download weights on first run if volume is empty
if [ ! -f "$MARKER" ]; then
    echo "[OmniParser] Downloading model weights (~4GB). This only happens once..."
    mkdir -p "$WEIGHTS_DIR/icon_detect" "$WEIGHTS_DIR/icon_caption_florence"

    hf download microsoft/OmniParser-v2.0 icon_detect/train_args.yaml --local-dir "$WEIGHTS_DIR"
    hf download microsoft/OmniParser-v2.0 icon_detect/model.pt --local-dir "$WEIGHTS_DIR"
    hf download microsoft/OmniParser-v2.0 icon_detect/model.yaml --local-dir "$WEIGHTS_DIR"
    hf download microsoft/OmniParser-v2.0 icon_caption/config.json --local-dir "$WEIGHTS_DIR"
    hf download microsoft/OmniParser-v2.0 icon_caption/generation_config.json --local-dir "$WEIGHTS_DIR"
    hf download microsoft/OmniParser-v2.0 icon_caption/model.safetensors --local-dir "$WEIGHTS_DIR"

    # Rearrange icon_caption -> icon_caption_florence
    if [ -d "$WEIGHTS_DIR/icon_caption" ]; then
        rm -rf "$WEIGHTS_DIR/icon_caption_florence"
        mv "$WEIGHTS_DIR/icon_caption" "$WEIGHTS_DIR/icon_caption_florence"
    fi

    touch "$MARKER"
    echo "[OmniParser] Weights downloaded successfully."
else
    echo "[OmniParser] Weights already present, skipping download."
fi

echo "[OmniParser] Starting Gradio server on port 7861..."
exec python -u -m gradio_demo
