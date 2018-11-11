FROM python:2.7-stretch

WORKDIR /trump2cash

# Install the dependencies.
ADD requirements.txt .
RUN pip install -r requirements.txt

# Add the source.
ADD analysis.py .
ADD logs.py .
ADD main.py .
ADD trading.py .
ADD twitter.py .

# Expose the port for monitoring. Run with "-p 80:80".
EXPOSE 80

# Run the app.
ENTRYPOINT ["python", "main.py"]
