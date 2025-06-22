# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script itself into the container
COPY definitive_chunker.py .
# If you are using a .env file to define bucket names, also copy it:
# COPY .env .

# Define the command to run your script when the container starts
# This makes it an executable command within the container.
# We'll run it specifically when the Cloud Run service is invoked.
ENTRYPOINT ["python", "definitive_chunker.py"]