FROM python:3.4-alpine
EXPOSE 5000

COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /app
COPY app.py parser.py ./
COPY templates ./templates
USER nobody
ENTRYPOINT ["python", "app.py"]
