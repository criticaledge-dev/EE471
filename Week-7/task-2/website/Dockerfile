FROM python:3.12.11-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py baseline_metrics.json optimized_metrics.json ./
COPY templates ./templates
COPY static ./static
RUN useradd --uid 10001 --create-home web
USER web
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "75", "app:app"]
