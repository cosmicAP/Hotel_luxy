FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN chmod +x /app/entrypoint.sh

RUN mkdir -p /app/staticfiles && \
    python manage.py collectstatic --noinput --clear

RUN mkdir -p /app/media && chmod 755 /app/media

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
