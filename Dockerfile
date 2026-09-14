# Docker configuration for the GitHub Issues Service.
#
# This Dockerfile:
# * uses Python 3.14 slim as the base image;
# * installs the application's Python dependencies;
# * copies the FastAPI application into the container;
# * exposes port 8000; and
# * starts the application with Uvicorn.
#
# Author: Thanzeel Hassan

FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
