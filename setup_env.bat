@echo off
REM Extract API key from test.txt and set as environment variable

echo Setting up OpenAI API Key environment variable...

REM Check if test.txt exists
if not exist "test.txt" (
    echo ERROR: test.txt not found!
    exit /b 1
)

REM Extract the Bearer token from test.txt
for /f "tokens=*" %%a in ('findstr /C:"Bearer sk-" test.txt') do (
    set LINE=%%a
)

REM Parse the API key from the Authorization header line
for /f "tokens=3 delims= " %%b in ('echo %LINE%') do (
    set API_KEY=%%b
)

REM Remove trailing quote if present
set API_KEY=%API_KEY:"=%

if "%API_KEY%"=="" (
    echo ERROR: Could not extract API key from test.txt
    exit /b 1
)

REM Set the environment variable
set OPENAI_API_KEY=%API_KEY%

echo API Key has been set successfully!
echo Starting PowerShell with OPENAI_API_KEY environment variable...
echo.

REM Start PowerShell with the environment variable
powershell.exe -NoExit -Command "$env:OPENAI_API_KEY='%API_KEY%'; Write-Host 'Environment variable OPENAI_API_KEY is now set for this session' -ForegroundColor Green; Write-Host 'You can now run your Python scripts' -ForegroundColor Green"
