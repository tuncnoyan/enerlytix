FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY django_app/requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# Copy project
COPY django_app/ /app/
COPY .env /app/.env 2>/dev/null || true

# Create necessary directories
RUN mkdir -p /app/static /app/media /app/logs

# Collect static files
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
