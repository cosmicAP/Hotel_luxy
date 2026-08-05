FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN mkdir -p /app/staticfiles && \
    python manage.py collectstatic --noinput --clear

RUN mkdir -p /app/media && chmod 755 /app/media

EXPOSE 80

CMD gunicorn hotel_project.wsgi:application \
    --bind 0.0.0.0:${PORT:-80} \
    --workers 3 \
    --threads 2 \
    --access-logfile - \
    --error-logfile -

