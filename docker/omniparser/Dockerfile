FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_ENABLE_HF_TRANSFER=1 \
    PIP_TIMEOUT=600 \
    PIP_PROGRESS_BAR=off

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Clone OmniParser
RUN git clone -b CraftOS https://github.com/zfoong/OmniParser_CraftOS.git /app/OmniParser

WORKDIR /app/OmniParser

# Install PyTorch CPU — large wheel (~700MB), extraction takes several minutes with no visible progress
RUN pip install --no-cache-dir --timeout 600 \
    torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu

# Install OmniParser dependencies
RUN pip install --no-cache-dir --timeout 300 \
    mkl==2024.0 sympy==1.13.1 transformers==4.51.0 \
    huggingface_hub[cli] hf_transfer \
    && pip install --no-cache-dir --timeout 300 -r requirements.txt

COPY docker/omniparser/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 7861

ENTRYPOINT ["/entrypoint.sh"]
