FROM python:3.11

WORKDIR /app
RUN mkdir -p /secrets
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:application"]