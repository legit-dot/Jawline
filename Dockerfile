# Start from a clean, stable Python 3.10 image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# --- NEW BLOCK: Install system libraries for MediaPipe/OpenCV ---
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
# ----------------------------------------------------------------

# Copy the requirements file and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose the port
EXPOSE 8080

# Run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]