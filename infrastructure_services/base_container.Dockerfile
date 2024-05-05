FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

#COPY data_generator.py /app
#
#RUN mkdir -p /app/data
#
#CMD ["python", "data_generator.py"]