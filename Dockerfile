# Use an official Python runtime as a parent image bla
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0


# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port available to the world outside this container
EXPOSE 5000


# Run app.py when the container launches
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
