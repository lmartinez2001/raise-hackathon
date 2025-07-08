from multiprocessing import cpu_count

# Socket path
bind = "unix:/home/ubuntu/hackathon/backend/gunicorn.sock"

# Worker options
workers = cpu_count() + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Logging options
loglevel = "info"
accesslog = "/home/ubuntu/hackathon/backend/access.log"
errorlog = "/home/ubuntu/hackathon/backend/error.log"

# Security
user = "ubuntu"
group = "www-data"

# Performance
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
timeout = 30
