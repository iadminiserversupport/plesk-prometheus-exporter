FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY plesk_exporter ./plesk_exporter
EXPOSE 9784
USER nobody
CMD ["python", "-m", "plesk_exporter.exporter"]
