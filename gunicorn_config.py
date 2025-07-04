# Gunicorn configuration file
# To use this configuration, run gunicorn with:
# gunicorn sortownia_project.wsgi:application --config=gunicorn_config.py

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
# A good rule of thumb is 2-4 x number of CPU cores
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"

# Timeout settings
# Increase timeout to prevent worker timeout errors
# Default is 30 seconds
timeout = 120  # Increase to 2 minutes

# Prevent worker timeout errors when a request takes too long
graceful_timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "sortownia"

# Limit the number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Reduce server load by recycling workers
worker_connections = 1000
worker_tmp_dir = "/dev/shm"  # Use shared memory for temporary files

# Set some performance tuning parameters
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Pre-load application code before forking
preload_app = True

# Avoid some known types of worker deadlock
forwarded_allow_ips = "*"
secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
}

# Process management
reload = True

# Worker settings to make the application more robust
worker_exit_on_graceful_deregister = True

# Timeout configuration for worker processes
graceful_timeout = 120  # Graceful worker timeout in seconds
timeout = 120  # Worker timeout in seconds