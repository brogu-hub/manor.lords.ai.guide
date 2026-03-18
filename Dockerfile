FROM python:3.12-slim

WORKDIR /app

# Install build tools for ooz (Oodle Kraken decompressor)
RUN apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends \
        g++ curl xz-utils ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Build ooz (open-source Oodle Kraken decompressor) as shared library
RUN curl -sL https://github.com/rarten/ooz/archive/refs/heads/master.tar.gz | \
    tar xz -C /opt && \
    cd /opt/ooz-master && \
    g++ -O2 -shared -fPIC -o /opt/libooz.so \
        kraken.cpp lzna.cpp bitknit.cpp stdafx.cpp \
        compress.cpp compr_entropy.cpp compr_kraken.cpp \
        compr_leviathan.cpp compr_mermaid.cpp compr_multiarray.cpp \
        compr_tans.cpp compr_match_finder.cpp \
        -lpthread && \
    rm -rf /opt/ooz-master

# Install uesave (pre-downloaded binary)
COPY uesave.tar.xz /tmp/uesave.tar.xz
RUN tar xJf /tmp/uesave.tar.xz -C /tmp/ && \
    mv /tmp/uesave_cli-x86_64-unknown-linux-gnu/uesave /usr/local/bin/uesave && \
    chmod +x /usr/local/bin/uesave && \
    rm -rf /tmp/uesave*

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code is bind-mounted at runtime, not copied
CMD ["uvicorn", "src.dashboard.app:app", "--host", "0.0.0.0", "--port", "7861", "--reload"]
