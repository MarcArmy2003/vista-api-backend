# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim-buster

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Run the web service on container startup.
# Cloud Run services must listen on the port defined by the PORT environment variable.
# gunicorn is a production-ready WSGI HTTP Server.
# The 'app:app' specifies that gunicorn should run the 'app' Flask instance from the 'app.py' file.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app