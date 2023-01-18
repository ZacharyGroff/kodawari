FROM python:3.11.1-buster
WORKDIR /service
COPY . .
RUN pip3 install poetry
RUN poetry install --no-dev --no-root
CMD ["poetry", "run", "uvicorn", "main:app", "--app-dir", "user_api/", "--host", "0.0.0.0"]
