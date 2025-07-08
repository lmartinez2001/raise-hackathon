from multiprocessing import cpu_count

# Socket path
bind = "unix:/var/run/raise/backend/gunicorn.sock"

# Worker options
workers = cpu_count() + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Logging options
loglevel = "info"
accesslog = "/home/louis/raise/backend/access.log"
errorlog = "/home/louis/raise/backend/error.log"

# Security
user = "louis"
group = "www-data"

# Performance
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
timeout = 30
