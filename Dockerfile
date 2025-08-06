## Parent image
FROM python:3.10-slim

## Essential environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

## Work directory inside the docker container
WORKDIR /app

## Installing system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

## Copying all contents from local to /app in container
COPY . .

## Run setup.py (for editable install if using setup.py)
RUN pip install --no-cache-dir -e .

## Expose Flask port
EXPOSE 5000

## Run the app
CMD ["python", "app.py"] 