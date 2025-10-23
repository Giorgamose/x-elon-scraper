@echo off
REM Script to push x-elon-scraper to GitHub
REM
REM BEFORE RUNNING THIS:
REM 1. Create a new repository on GitHub: https://github.com/new
REM    - Name: x-elon-scraper
REM    - DO NOT initialize with README, .gitignore, or license
REM 2. Replace YOUR_USERNAME below with your actual GitHub username

echo ========================================
echo   X Elon Scraper - GitHub Push Script
echo ========================================
echo.

REM Ask for GitHub username
set /p GITHUB_USERNAME="Enter your GitHub username: "

if "%GITHUB_USERNAME%"=="" (
    echo Error: GitHub username cannot be empty!
    pause
    exit /b 1
)

echo.
echo Configuring git...
git config user.name "%GITHUB_USERNAME%"
git config user.email "%GITHUB_USERNAME%@users.noreply.github.com"

echo.
echo Adding remote repository...
git remote add origin https://github.com/%GITHUB_USERNAME%/x-elon-scraper.git

echo.
echo Renaming branch to main...
git branch -M main

echo.
echo Pushing to GitHub...
echo You may be prompted for your GitHub credentials.
echo Note: Use a Personal Access Token instead of password.
echo Get token at: https://github.com/settings/tokens
echo.
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   SUCCESS! Repository pushed to GitHub
    echo ========================================
    echo.
    echo View your repository at:
    echo https://github.com/%GITHUB_USERNAME%/x-elon-scraper
    echo.
    echo Don't forget to:
    echo - Add a description on GitHub
    echo - Add topics: python, fastapi, react, docker
    echo - Star your own repo!
    echo.
) else (
    echo.
    echo ========================================
    echo   ERROR: Push failed
    echo ========================================
    echo.
    echo Common solutions:
    echo 1. Make sure you created the repository on GitHub first
    echo 2. Check your GitHub username is correct
    echo 3. Use a Personal Access Token instead of password
    echo 4. If "remote origin already exists", run:
    echo    git remote remove origin
    echo    Then run this script again
    echo.
)

pause
