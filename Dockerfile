# Use an official Python runtime as a parent image
FROM python:2.7-slim
MAINTAINER David Scrobonia

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Define environment variable
#ENV NAME World

# Run app.py when the container launches
CMD ["python", "api.py"]
