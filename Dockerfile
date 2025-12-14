# Start from a clean, stable Python 3.10 image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies first
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose the port where the Flask/Gunicorn app runs
EXPOSE 8080

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]