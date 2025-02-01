@echo off
setlocal enabledelayedexpansion

set "DEADLINE_DIR=C:\DeadlineRepository10"
set "PLUGIN_DIR=%~dp0"

if "%DEADLINE_DIR%"=="" (
    echo Deadline directory path is required.
    exit /b 1
)

if not exist "%PLUGIN_DIR%plugins" (
    echo Plugins directory not found: %PLUGIN_DIR%plugins
    exit /b 1
)
if not exist "%PLUGIN_DIR%scripts" (
    echo Scripts directory not found: %PLUGIN_DIR%scripts
    exit /b 1
)

if not exist "%DEADLINE_DIR%\custom\plugins" (
    mkdir "%DEADLINE_DIR%\custom\plugins"
)

:: Create symbolic links for plugins folders
for /d %%D in ("%PLUGIN_DIR%plugins\*") do (
    set "PLUGIN_NAME=%%~nxD"
    if not exist "%DEADLINE_DIR%\custom\plugins\!PLUGIN_NAME!" (
        mklink /D "%DEADLINE_DIR%\custom\plugins\!PLUGIN_NAME!" "%%D"
    )
)

:: Link script files from direct subfolders only
for /d %%D in ("%PLUGIN_DIR%scripts\*") do (
    set "FOLDER_NAME=%%~nxD"
    if not exist "%DEADLINE_DIR%\custom\scripts\!FOLDER_NAME!" (
        mkdir "%DEADLINE_DIR%\custom\scripts\!FOLDER_NAME!" 2>nul
    )
    
    for %%F in ("%%D\*") do (
        set "FILE_NAME=%%~nxF"
        if not exist "%DEADLINE_DIR%\custom\scripts\!FOLDER_NAME!\!FILE_NAME!" (
            mklink "%DEADLINE_DIR%\custom\scripts\!FOLDER_NAME!\!FILE_NAME!" "%%F"
        )
    )
)

echo Synchronization completed successfully.
exit /b 0