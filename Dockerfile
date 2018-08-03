FROM python:2.7-stretch

WORKDIR /app
ADD . /app

# Install the dependencies.
RUN pip install -r requirements.txt

# Expose the port for monitoring. Run with "-p 80:80".
EXPOSE 80

# Run the app.
ENTRYPOINT ["python", "main.py"]
