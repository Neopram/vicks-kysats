# Lanza todas las oleadas autónomamente
# Uso: .\launch-waves.ps1

param(
    [switch]$DryRun = $false
)

Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " VICKS KYSATS 2026 — Oleadas Autónomas" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Verifica Python
try {
    $python = python --version 2>&1 | Select-Object -First 1
    Write-Host "✓ Python: $python" -ForegroundColor Green
} catch {
    Write-Host "✗ Python no disponible" -ForegroundColor Red
    exit 1
}

# Verifica git
try {
    $git = git --version 2>&1 | Select-Object -First 1
    Write-Host "✓ Git: $git" -ForegroundColor Green
} catch {
    Write-Host "✗ Git no disponible" -ForegroundColor Red
    exit 1
}

# Verifica API key de Anthropic
if (-not $env:ANTHROPIC_API_KEY) {
    Write-Host "⚠️  Falta ANTHROPIC_API_KEY en variables de entorno" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ ANTHROPIC_API_KEY configurada" -ForegroundColor Green

Write-Host ""
Write-Host "Iniciando oleadas..." -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "[DRY RUN] No se ejecutarán comandos" -ForegroundColor Yellow
    exit 0
}

# Lanza oleadas
& python scripts/vicks_autonomous_waves.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Oleadas completadas exitosamente" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ver apps en:" -ForegroundColor Cyan
    Write-Host "  • neopram.github.io/vicks-kysats/patologia" -ForegroundColor White
    Write-Host "  • neopram.github.io/vicks-kysats/pediatria" -ForegroundColor White
    Write-Host "  • neopram.github.io/vicks-kysats/cirugia" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "✗ Error en oleadas (code: $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}
