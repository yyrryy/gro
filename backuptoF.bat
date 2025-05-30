@echo off
setlocal enabledelayedexpansion

set DATABASE_NAME=orghdata
set USER=postgres
set BACKUP_DIR=C:\backups
set EXTERNAL_SSD_DRIVE=D:
set EXTERNAL2=F:
set EXTERNAL3=G:



set TIMESTAMP=!DAY!!MONTH!!YEAR!

set BACKUP_FILE=%BACKUP_DIR%\backup.sql

echo Backing up database %DATABASE_NAME%...

REM Set PGPASSFILE environment variable to point to .pgpass file
set PGPASSFILE=C:\Users\Public\pgpass.conf

"C:\bin\pg_dump.exe" -h localhost -U %USER% -b -v -f "%BACKUP_FILE%" %DATABASE_NAME%
echo Backup completed.

echo Copying backup to external SSD drive %EXTERNAL_SSD_DRIVE%...
copy "%BACKUP_FILE%" %EXTERNAL_SSD_DRIVE%
copy "%BACKUP_FILE%" %EXTERNAL2%
echo Copy completed.
endlocal