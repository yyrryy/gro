@echo off
start /B waitress-serve --port=80 Gro.wsgi:application
