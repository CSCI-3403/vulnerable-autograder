import multiprocessing

max_requests = 1000
max_requests_jitter = 50

log_file = "-"

host = "0.0.0.0"
port = 8000
#workers = 1
workers = multiprocessing.cpu_count() * 2 + 1
proc_name = "autograder_web"
