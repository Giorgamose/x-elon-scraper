# PowerShell script to push x-elon-scraper to GitHub
#
# BEFORE RUNNING THIS:
# 1. Create a new repository on GitHub: https://github.com/new
#    - Name: x-elon-scraper
#    - DO NOT initialize with README, .gitignore, or license
# 2. Have your GitHub username ready

Write-Host "========================================"
Write-Host "  X Elon Scraper - GitHub Push Script"
Write-Host "========================================"
Write-Host ""

# Change to project directory
Set-Location -Path "C:\Users\gmaevski\Documents\X Scrapper\x-elon-scraper"

# Ask for GitHub username
$githubUsername = Read-Host "Enter your GitHub username"

if ([string]::IsNullOrWhiteSpace($githubUsername)) {
    Write-Host "Error: GitHub username cannot be empty!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Configuring git..." -ForegroundColor Cyan
git config user.name $githubUsername
git config user.email "$githubUsername@users.noreply.github.com"

Write-Host ""
Write-Host "Adding remote repository..." -ForegroundColor Cyan
$remoteUrl = "https://github.com/$githubUsername/x-elon-scraper.git"

# Check if remote already exists
$existingRemote = git remote get-url origin 2>$null

if ($existingRemote) {
    Write-Host "Remote 'origin' already exists: $existingRemote" -ForegroundColor Yellow
    $replace = Read-Host "Replace it? (y/n)"
    if ($replace -eq 'y') {
        git remote remove origin
        git remote add origin $remoteUrl
    }
} else {
    git remote add origin $remoteUrl
}

Write-Host ""
Write-Host "Renaming branch to main..." -ForegroundColor Cyan
git branch -M main

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
Write-Host "You may be prompted for your GitHub credentials." -ForegroundColor Yellow
Write-Host "Note: Use a Personal Access Token instead of password." -ForegroundColor Yellow
Write-Host "Get token at: https://github.com/settings/tokens" -ForegroundColor Yellow
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  SUCCESS! Repository pushed to GitHub" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "View your repository at:" -ForegroundColor Cyan
    Write-Host "https://github.com/$githubUsername/x-elon-scraper" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Don't forget to:" -ForegroundColor Yellow
    Write-Host "- Add a description on GitHub"
    Write-Host "- Add topics: python, fastapi, react, docker, twitter"
    Write-Host "- Star your own repo!"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ERROR: Push failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "1. Make sure you created the repository on GitHub first"
    Write-Host "2. Check your GitHub username is correct"
    Write-Host "3. Use a Personal Access Token instead of password"
    Write-Host "4. If 'remote origin already exists', run:"
    Write-Host "   git remote remove origin"
    Write-Host "   Then run this script again"
    Write-Host ""
}

Read-Host "Press Enter to exit"
