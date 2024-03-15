FROM python:latest

WORKDIR /src

COPY . .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

ENTRYPOINT ["uvicorn", "app.appController:app", "--host", "0.0.0.0", "--port", "8000"]