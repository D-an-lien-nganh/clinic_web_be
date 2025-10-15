# Check whether website in development or production statge
import socket
PRODUCTION_SERVERS = ['985313-01']

def check_env():
    for item in PRODUCTION_SERVERS:
        match = item == socket.gethostname()
        if match:
            return True

if check_env():
    PRODUCTION = True
else:
    PRODUCTION = False

if PRODUCTION:
    from .prod import *
else:
    from .dev import *
