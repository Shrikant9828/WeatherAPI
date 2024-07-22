# Use Python 3.11.4 slim Debian Bullseye as the base image
FROM python:3.11.4-slim-bullseye

# Set environment variable to ensure Python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED 1

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory in the container
WORKDIR /home/app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose port 8000 to allow external access to the application
EXPOSE 8000

# Make the start script executable
RUN chmod +x ./start

# Set the command to run when the container starts
CMD ["/home/app/start"]