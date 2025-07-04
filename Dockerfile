FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

COPY gunicorn_config.py .
CMD ["gunicorn", "sortownia_project.wsgi:application", "--config", "gunicorn_config.py"]