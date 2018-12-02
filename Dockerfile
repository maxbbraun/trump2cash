FROM python:3-stretch

WORKDIR /trump2cash

# Install the dependencies.
ADD requirements.txt .
RUN pip3 install -r requirements.txt

# Add the source.
ADD *.py ./

# Expose the port for monitoring. Run with "-p 80:80".
EXPOSE 80

# Run the app.
ENTRYPOINT ["python", "main.py"]
