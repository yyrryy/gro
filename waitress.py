# import os
# from threading import Thread
# from time import sleep
# import subprocess
# import sys

# # os.system('start /B waitress-serve 192.168.1.8 --port=80 Gro.wsgi:application')
# def runserver():
#     os.system('waitress-serve --host=192.168.1.8 --port=80 Gro.wsgi:application')

# def lunchchrome():
#     # ensure the django server is up and running
#     sleep(2)
#     # get ipv4 address
#     os.system('start chrome http://192.168.1.8')
# t1=Thread(target=runserver)

# t2=Thread(target=lunchchrome)

# t1.start()
# sleep(2)
# t2.start()

import subprocess
import socket
from threading import Thread
from time import sleep


HOST = "192.168.1.8"
PORT = 80


def runserver():
    """
    Start Waitress server with optimized settings
    """
    subprocess.Popen([
        "waitress-serve",
        f"--host={HOST}",
        f"--port={PORT}",
        "--threads=8",
        "--connection-limit=200",
        "--channel-timeout=30",
        "Gro.wsgi:application"
    ])


def wait_for_server(host, port):
    """
    Wait until server is actually accepting connections
    """
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                break
        except OSError:
            sleep(1)


def launch_chrome():
    """
    Open browser only after server is ready
    """
    wait_for_server(HOST, PORT)
    subprocess.Popen([
        "cmd", "/c", "start", "chrome", f"http://{HOST}"
    ])


if __name__ == "__main__":
    t1 = Thread(target=runserver)
    t2 = Thread(target=launch_chrome)

    t1.start()
    sleep(1)  # small buffer
    t2.start()

    t1.join()
    t2.join()