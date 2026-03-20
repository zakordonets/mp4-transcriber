# MP4 Transcriber - GitHub Upload Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MP4 Transcriber - GitHub Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check git
$gitVersion = git --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Git found: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "Git not found! Install from https://git-scm.com/" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Initializing Git repository..." -ForegroundColor Yellow

if (-not (Test-Path ".git")) {
    git init
    Write-Host "Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "Git repository already exists" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Adding files to git..." -ForegroundColor Yellow
git add .
Write-Host "All files staged" -ForegroundColor Green

Write-Host ""
Write-Host "Creating initial commit..." -ForegroundColor Yellow
git commit -m "Initial commit: MP4 Transcriber v1.0"
Write-Host "Commit created" -ForegroundColor Green

Write-Host ""
Write-Host "Setting branch to main..." -ForegroundColor Yellow
git branch -M main
Write-Host "Branch set to main" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Local Git Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Go to https://github.com/new" -ForegroundColor White
Write-Host "2. Create repo named: mp4-transcriber" -ForegroundColor White
Write-Host "3. DO NOT add README, .gitignore, or license" -ForegroundColor White
Write-Host "4. Run the commands GitHub shows you:" -ForegroundColor White
Write-Host ""
Write-Host "git remote add origin https://github.com/YOUR_USERNAME/mp4-transcriber.git" -ForegroundColor Cyan
Write-Host "git push -u origin main" -ForegroundColor Cyan
Write-Host ""
