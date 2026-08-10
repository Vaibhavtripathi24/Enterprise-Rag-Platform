FROM python:3.11-slim-bookworm

# Pull uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN python3 -c "import tomllib,subprocess; deps=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']; subprocess.run(['uv','pip','install','--system','--no-cache']+deps,check=True)"

COPY app/ ./app/
COPY ui/ ./ui/
COPY start.sh ./start.sh

RUN chmod +x ./start.sh

# Expose Streamlit port
EXPOSE 8501
EXPOSE 8000

# Run as non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["bash", "start.sh"]
