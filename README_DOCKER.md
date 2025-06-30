# Docker Setup for Sortownia

This document explains how to run the Sortownia application using Docker and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd Sortownia
   ```

2. Make sure you have a `.env` file in the project root with the following content:
   ```
   POSTGRES_DB=sortownia
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   DATABASE_URL=postgres://postgres:postgres@db:5432/sortownia
   SECRET_KEY=django-insecure-sortownia-secret-key-12345
   DEBUG=True
   ```
   Note: For production, change the `SECRET_KEY` and set `DEBUG=False`.

## Usage

### Start the Application

```
docker-compose up -d
```

This will:
- Build the Docker image for the application
- Start a PostgreSQL database container
- Start the Django application container
- Map port 8000 on your host to the application

### Access the Application

Open your browser and navigate to:
```
http://localhost:8000
```

### Run Migrations

When running for the first time, you need to run migrations:
```
docker-compose exec web python manage.py migrate
```

### Create a Superuser

```
docker-compose exec web python manage.py createsuperuser
```

### Collect Static Files

```
docker-compose exec web python manage.py collectstatic --noinput
```

### View Logs

```
docker-compose logs -f
```

### Stop the Application

```
docker-compose down
```

## Data Persistence

The PostgreSQL data is stored in the `postgres_data` directory on your local machine, which is mapped to the container. This ensures that your data persists even when the containers are removed.

## Port Configuration

The PostgreSQL database is configured to use port 5433 on the host machine to avoid conflicts with any existing PostgreSQL installations. Inside the Docker network, the containers still communicate using the standard PostgreSQL port (5432).

If you need to connect to the database from your host machine:
```
psql -h localhost -p 5433 -U postgres -d sortownia
```

## Customization

If you need to customize the Docker setup, you can modify:
- `Dockerfile` for application container configuration
- `docker-compose.yml` for service configuration

## Troubleshooting

1. If you encounter permission issues with the `postgres_data` directory, you might need to change its ownership:
   ```
   sudo chown -R $USER:$USER postgres_data
   ```

2. If the web service fails to connect to the database, ensure the database service is fully initialized before the web service tries to connect.

3. If port 5433 is also in use on your host machine, you can modify the `docker-compose.yml` file to use a different port, such as 5434 or another available port.