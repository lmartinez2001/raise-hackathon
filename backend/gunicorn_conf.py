from multiprocessing import cpu_count

# Socket path
bind = "unix:/var/run/raise/backend/gunicorn.sock"

# Worker options
workers = cpu_count() + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Logging options
loglevel = "debug"
accesslog = "/home/louis/raise/backend/access.log"
errorlog = "/home/louis/raise/backend/error.log"
