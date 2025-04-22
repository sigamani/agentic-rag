FROM nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface

# Install OS packages
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    python3.10 \
    python3.10-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set Python aliases
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
RUN python -m pip install --upgrade pip setuptools wheel

# Copy project
WORKDIR /workspace
COPY . /workspace

# Create and activate virtual environment
RUN python -m venv venv
ENV PATH="/workspace/venv/bin:$PATH"

# Install Python requirements
RUN pip install -r requirements-ft.txt

# Default command (can be overridden)
CMD ["bash", "run_all.sh"]

