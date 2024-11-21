FROM python:3.11

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

RUN chmod +x /app/pipeline.sh

CMD ["/app/pipeline.sh"]
