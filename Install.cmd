@echo off
setlocal

title TTS BSR Setup
echo Setting up required files for the TTS BSR
echo.

rem -------------------------------
rem Check Python 3.12.5
rem -------------------------------
echo Checking for Python 3.12.5...
for /f "tokens=2 delims= " %%v in ('py -3.12 --version 2^>nul') do set PY_VER=%%v

if "%PY_VER%"=="3.12.5" (
    echo Python 3.12.5 detected.
) else (
    echo Python 3.12.5 not found, downloading and installing...

    set "PYTHON_INSTALLER=%TEMP%\python-3.12.5-amd64.exe"

    rem Download Python installer silently
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.12.5/python-3.12.5-amd64.exe -OutFile '%PYTHON_INSTALLER%'"

    if not exist "%PYTHON_INSTALLER%" (
        echo Failed to download Python installer.
        pause
        exit /b 1
    )

    rem Install Python silently for current user without UAC
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
    del "%PYTHON_INSTALLER%"

    rem Refresh environment variables to include python
    set "PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python312\Scripts;%USERPROFILE%\AppData\Local\Programs\Python\Python312;%PATH%"

    rem Confirm install
    for /f "tokens=2 delims= " %%v in ('py -3.12 --version 2^>nul') do set PY_VER=%%v

    if not "%PY_VER%"=="3.12.5" (
        echo Failed to install Python 3.12.5.
        pause
        exit /b 1
    )
    echo Python 3.12.5 installed successfully.
)

echo.
echo Installing required Python packages...

rem -------------------------------
rem Install ffmpeg executable
rem -------------------------------
echo Installing ffmpeg executable...

rem Check if ffmpeg is already available
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo FFmpeg already available in PATH.
    goto :ffmpeg_installed
)

rem Download FFmpeg using curl (much faster than PowerShell)
echo Downloading FFmpeg using curl...

set "FFMPEG_DIR=C:\ffmpeg-7.1.1-essentials_build"

rem Download using curl (built into Windows 10+)
curl -L -o "%TEMP%\ffmpeg.zip" "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-7.1.1-essentials_build.zip"
if exist "%TEMP%\ffmpeg.zip" (
    rem Extract entire zip to C:\
    powershell -Command "Expand-Archive -Path '%TEMP%\ffmpeg.zip' -DestinationPath 'C:\' -Force"
    
    rem Add bin directory to current session PATH
    set "PATH=%FFMPEG_DIR%\bin;%PATH%"
    
    rem Add to permanent system PATH using PowerShell (requires admin)
powershell -Command "Start-Process powershell -ArgumentList '-Command', '[Environment]::SetEnvironmentVariable(\"PATH\", [Environment]::GetEnvironmentVariable(\"PATH\", \"Machine\") + \";C:\\ffmpeg-7.1.1-essentials_build\\bin\", \"Machine\")' -Verb RunAs" -Wait
    
    rem Clean up
    del "%TEMP%\ffmpeg.zip" >nul 2>&1
    rmdir /s /q "%TEMP%\ffmpeg-7.1.1-essentials_build" >nul 2>&1
    
    echo FFmpeg installed to %FFMPEG_DIR% with full directory structure and added to system PATH
) else (
    echo Failed to download ffmpeg
    pause
    exit /b 1
)

:ffmpeg_installed
rem Verify FFmpeg installation
echo Verifying FFmpeg installation...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: FFmpeg verification failed!
    pause
    exit /b 1
)
echo FFmpeg verification successful.

ffprobe -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: FFprobe verification failed!
    pause
    exit /b 1
)
echo FFprobe verification successful.

rem -------------------------------
rem Install all packages in one command
rem -------------------------------
py -3.12 -m pip install asyncio==4.0.0 requests==2.32.3 websockets==12.0 psutil==7.0.0 pydub==0.25.1 pycaw==20240210 comtypes==1.4.11 pygame==2.6.1 watchdog==5.0.2 packaging==24.1 --user --disable-pip-version-check

rem Clean up any data folder created in wrong location during package installation
if exist "data" (
    rmdir /s /q "data" >nul 2>&1
    echo Cleaned up data folder created in wrong location.
)

echo.
echo Creating shortcut in installation folder...

set "SCRIPT_DIR=%~dp0"
set "TARGET=%SCRIPT_DIR%TTS BSR v4 13\tts_gui_v4.pyw"
set "SHORTCUT=%SCRIPT_DIR%Run TTS BSR.lnk"

rem Path to pythonw.exe installed by your earlier steps
set "PYTHONW=%USERPROFILE%\AppData\Local\Programs\Python\Python312\pythonw.exe"

powershell -Command ^
"$ws = New-Object -ComObject WScript.Shell; ^
 $s = $ws.CreateShortcut('%SHORTCUT%'); ^
 $s.TargetPath = '%PYTHONW%'; ^
 $s.Arguments = '\"%TARGET%\"'; ^
 $s.WorkingDirectory = '%SCRIPT_DIR%TTS BSR v4 13'; ^
 $s.IconLocation = '%SCRIPT_DIR%TTS BSR v4 13\OIG3_10.ico'; ^
 $s.Save()"

echo.
echo Setup complete. Press any key to exit...
pause >nul
exit /b
