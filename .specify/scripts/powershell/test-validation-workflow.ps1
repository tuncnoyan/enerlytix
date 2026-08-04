# Test Validation Workflow Script for Feature 012
#
# Purpose: Run the validation workflow test suites in Docker only.
#
# Usage:
#   powershell .specify/scripts/powershell/test-validation-workflow.ps1
#   powershell .specify/scripts/powershell/test-validation-workflow.ps1 -Failfast -Verbosity 2
#
# Exit Code:
#   0 = All tests passed
#   1 = Tests failed or Docker is unavailable

param(
    [ValidateSet("0", "1", "2", "3")]
    [string]$Verbosity = "1",
    [switch]$Failfast = $false
)

$ErrorActionPreference = "Stop"

# Resolve repository root for consistent execution from any working directory.
$RepoRoot = git rev-parse --show-toplevel 2>$null
if (-not $RepoRoot) {
    $RepoRoot = (Get-Item -Path $PSScriptRoot).Parent.Parent.Parent.FullName
}

$ComposeFile = Join-Path $RepoRoot "django_app/docker/docker-compose.yml"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Report Validation Workflow Test Runner" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"
Write-Host ""

if (-not (Test-Path $ComposeFile)) {
    Write-Host "ERROR: Docker compose file not found at $ComposeFile" -ForegroundColor Red
    exit 1
}

Write-Host "Checking Docker Compose availability..." -ForegroundColor Yellow
try {
    docker compose -f $ComposeFile ps | Out-Null
} catch {
    Write-Host "ERROR: Docker Compose is not available or services are not running." -ForegroundColor Red
    Write-Host "Start services first: docker compose -f django_app/docker/docker-compose.yml up -d --build" -ForegroundColor Red
    exit 1
}

$TestTargets = @(
    "sitesync.tests.test_report_validation_assignment",
    "sitesync.tests.test_report_validation_comments",
    "sitesync.tests.test_report_validation_page_status",
    "sitesync.tests.test_report_validation_final_gate",
    "sitesync.tests.test_report_validation_regrant_reopen",
    "sitesync.tests.test_saved_reports_validation_metadata"
)

$CommandParts = @("python", "manage.py", "test") + $TestTargets
if ($Failfast) {
    $CommandParts += "--failfast"
}
$CommandParts += "--verbosity=$Verbosity"

Write-Host "Running validation suites:" -ForegroundColor Green
Write-Host ($CommandParts -join " ")
Write-Host ""

& docker compose -f $ComposeFile exec -T web @CommandParts
$ExitCode = $LASTEXITCODE

if ($ExitCode -eq 0) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "SUCCESS: Validation workflow suites passed" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    exit 0
}

Write-Host "=========================================" -ForegroundColor Red
Write-Host "FAILED: Validation workflow suites failed" -ForegroundColor Red
Write-Host "=========================================" -ForegroundColor Red
exit 1
