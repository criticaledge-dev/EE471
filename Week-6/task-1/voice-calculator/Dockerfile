FROM python:3.12.9-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libasound2 libssl3 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
COPY app.py speech_service.py custom_classes.py container_server.py ./
COPY templates ./templates
COPY static ./static
RUN useradd --uid 10001 --create-home speech
USER speech
EXPOSE 5000
CMD ["python", "-B", "container_server.py"]
