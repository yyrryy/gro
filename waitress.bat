@echo off
start /B waitress-serve 192.168.1.8 --port=80 Gro.wsgi:application
