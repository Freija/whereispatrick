FROM python:3.4-alpine
EXPOSE 5000
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
