# auth_service/Dockerfile

FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .

# --- AÑADE --upgrade AQUÍ ---
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app ./app

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "app.main:app"]