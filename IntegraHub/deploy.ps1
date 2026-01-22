Write-Host "🚀 Iniciando despliegue de IntegraHub..." -ForegroundColor Cyan

# 1. Verificar .env
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creando archivo .env desde .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# 2. Verificar Carpetas de Datos
$dataDirs = @("data/inbox", "data/postgres")
foreach ($dir in $dataDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "📂 Carpeta creada: $dir" -ForegroundColor Green
    }
}

# 3. Limpieza (Opcional, para asegurar fresh start)
# docker-compose down

# 4. Construcción y Despliegue
Write-Host "🐳 Levantando contenedores (esto puede tardar unos minutos)..." -ForegroundColor Cyan
docker-compose up --build -d

if ($?) {
    Write-Host "✅ ¡Despliegue Exitoso!" -ForegroundColor Green
    Write-Host "   - API Pedidos: http://localhost:8001/docs"
    Write-Host "   - Demo Portal: http://localhost:8088/"
    Write-Host "   - API Métricas: http://localhost:8004/metrics"
    Write-Host "   - RabbitMQ UI: http://localhost:15672 (user/password)"
} else {
    Write-Host "❌ Error en el despliegue." -ForegroundColor Red
}
