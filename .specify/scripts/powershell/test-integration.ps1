# Test Integration Script for Platform Foundation (Phase 7 - T083)
# 
# Purpose: Execute comprehensive test suite in Docker environment
# Validates all user stories end-to-end across Phases 1-6
#
# Usage: powershell .specify/scripts/powershell/test-integration.ps1
#
# Exit Code:
#   0 = All tests passed
#   1 = Tests failed

param(
    [string]$Verbosity = "1",
    [switch]$Failfast = $false
)

$ErrorActionPreference = "Stop"

# Get repo root
$RepoRoot = git rev-parse --show-toplevel 2>$null
if (-not $RepoRoot) {
    $RepoRoot = (Get-Item -Path $PSScriptRoot).Parent.Parent.Parent.FullName
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Platform Foundation Integration Tests" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Verify Docker is running
Write-Host "Checking Docker environment..." -ForegroundColor Yellow
try {
    docker compose -f "$RepoRoot/django_app/docker/docker-compose.yml" ps | Out-Null
} catch {
    Write-Host "ERROR: Docker Compose not running" -ForegroundColor Red
    Write-Host "Please start Docker and try again" -ForegroundColor Red
    exit 1
}

# Build test command
$TestCommand = "python manage.py test"
if ($Failfast) {
    $TestCommand += " --failfast"
}
$TestCommand += " --verbosity=$Verbosity"

Write-Host "Running: $TestCommand" -ForegroundColor Green
Write-Host ""

# Execute tests
$Process = docker compose -f "$RepoRoot/django_app/docker/docker-compose.yml" exec -T web python manage.py test --verbosity=$Verbosity
$ExitCode = $LASTEXITCODE

# Check results
if ($ExitCode -eq 0) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "SUCCESS: All tests passed" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "FAILED: Some tests did not pass" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    exit 1
}
