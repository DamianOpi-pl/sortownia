# Dockerized Clothing Sorting System

This document provides instructions for running the Clothing Sorting System application using Docker.

## Prerequisites

- Docker installed on your machine
- Docker Compose installed on your machine

## Quick Start

1. Clone the repository and navigate to the project directory:

```bash
git clone <repository-url>
cd Sortownia
```

2. Build and start the Docker containers:

```bash
docker-compose up -d
```

3. Access the application at http://localhost:8000/

## Configuration

The Docker setup can be configured through environment variables in the `docker-compose.yml` file:

### Application Settings

- `DJANGO_DEBUG`: Set to `True` for development, `False` for production (default: `False`)
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of hosts that can access the application (default: `localhost,127.0.0.1`)
- `DJANGO_SECRET_KEY`: Secret key for Django application (default: a development key, should be changed in production)

### Creating a Superuser

To create an admin user automatically when the container starts, uncomment and configure these environment variables in `docker-compose.yml`:

```yaml
# - DJANGO_SUPERUSER_USERNAME=admin
# - DJANGO_SUPERUSER_PASSWORD=adminpass
# - DJANGO_SUPERUSER_EMAIL=admin@example.com
```

## Data Persistence

The Docker setup persists data in the following ways:

- Database: The SQLite database is stored in a volume at `./data/db.sqlite3`
- Static files: Static files are stored in a volume at `./staticfiles`

## Common Tasks

### Viewing Logs

To view application logs:

```bash
docker-compose logs -f web
```

### Executing Commands Inside the Container

To run Django management commands inside the container:

```bash
docker-compose exec web python manage.py <command>
```

Examples:

```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Make migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

### Stopping the Application

To stop the containers:

```bash
docker-compose down
```

### Rebuilding After Changes

If you make changes to the application code or dependencies:

```bash
docker-compose build
docker-compose up -d
```

## Using PostgreSQL (Optional)

For production use, you might want to switch from SQLite to PostgreSQL. To do this:

1. Uncomment the PostgreSQL configuration in `sortownia_project/settings.py`
3. Add PostgreSQL service to `docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=sortownia
    restart: always

  web:
    # ... existing web configuration
    depends_on:
      - db
    environment:
      # ... existing environment variables
      - DATABASE_URL=postgres://postgres:postgres@db:5432/sortownia
    volumes:
      - ./staticfiles:/app/staticfiles
      # Remove the data volume when using PostgreSQL

volumes:
  postgres_data:
```

3. Install the required dependencies by adding these to `requirements.txt`:
   ```
   psycopg2-binary==2.9.6
   dj-database-url==2.1.0
   ```

## Production Deployment Considerations

## Troubleshooting

### Volume Mount Issues

If you encounter an error about mounting volumes, particularly with the database file, ensure that:

1. The `data` directory exists in your project folder
2. If you previously had a different volume setup, you might need to remove the containers and volumes:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Database File Permissions

If you encounter permission issues with the database file, you can fix them with:

```bash
sudo chown -R $(id -u):$(id -g) ./data
```

## Production Deployment Considerations

For production deployment, consider:

1. Using proper secrets management (not hardcoded in files)
2. Setting up HTTPS/TLS
3. Configuring proper database backups
4. Setting up a reverse proxy (Nginx) in front of Gunicorn
5. Implementing health checks