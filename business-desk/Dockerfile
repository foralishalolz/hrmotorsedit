FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DESK_DATA_DIR=/data DESK_BIND=0.0.0.0 PORT=8080
WORKDIR /app
COPY requirements.txt requirements-vercel.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home desk && mkdir /data && chown desk:desk /data
COPY --chown=desk:desk domain.py business.py regional.py operations.py branding.py server.py hosted.py admin.py ./
COPY --chown=desk:desk static ./static
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python -c "import os,urllib.request; from urllib.parse import urlsplit; r=urllib.request.Request('http://127.0.0.1:8080/api/health',headers={'Host':urlsplit(os.environ['DESK_PUBLIC_ORIGIN']).netloc}); urllib.request.urlopen(r,timeout=3).read()"
CMD ["python", "hosted.py"]
