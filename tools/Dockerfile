FROM python:3.12.7-slim
LABEL authors="bartnyk"

RUN pip install poetry
WORKDIR /app
COPY . /app
RUN poetry install
EXPOSE 8000

ENTRYPOINT ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]