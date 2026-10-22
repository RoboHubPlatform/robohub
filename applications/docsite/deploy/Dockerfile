FROM python:3.12-slim

WORKDIR /app
COPY build/site /app/site

EXPOSE 8080
CMD ["python3", "-m", "http.server", "8080", "--directory", "/app/site"]
