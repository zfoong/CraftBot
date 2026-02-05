FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_ENABLE_HF_TRANSFER=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Clone OmniParser
RUN git clone -b CraftOS https://github.com/zfoong/OmniParser_CraftOS.git /app/OmniParser

WORKDIR /app/OmniParser

# Install PyTorch CPU (GPU users get CUDA at runtime via nvidia container toolkit)
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu

# Install OmniParser dependencies
RUN pip install --no-cache-dir \
    mkl==2024.0 sympy==1.13.1 transformers==4.51.0 \
    huggingface_hub[cli] hf_transfer \
    && pip install --no-cache-dir -r requirements.txt

COPY docker/omniparser/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 7861

ENTRYPOINT ["/entrypoint.sh"]
