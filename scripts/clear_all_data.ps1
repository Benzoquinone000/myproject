# 警告提示（UTF-8 BOM 避免 Windows PowerShell 中文乱码；路径相对项目根目录）
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "警告：此操作将清空所有数据库和中间件数据！" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
$confirm = Read-Host "确认要继续吗？(输入 'YES' 继续)"

if ($confirm -ne "YES") {
    Write-Host "操作已取消" -ForegroundColor Red
    exit 0
}

# 停止服务
Write-Host "正在停止 Docker 服务..." -ForegroundColor Cyan
docker compose down

# 清空 SQLite 数据库
Write-Host "正在清空 SQLite 数据库..." -ForegroundColor Cyan
Remove-Item -Path "saves\database\server.db" -ErrorAction SilentlyContinue
Get-ChildItem -Path "saves\agents" -Recurse -Filter "*.db*" | Remove-Item -Force

# 清空 Neo4j 数据
Write-Host "正在清空 Neo4j 数据..." -ForegroundColor Cyan
Remove-Item -Path "docker\volumes\neo4j\data\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "docker\volumes\neo4j\logs\*" -Recurse -Force -ErrorAction SilentlyContinue

# 清空 Milvus 数据
Write-Host "正在清空 Milvus 数据..." -ForegroundColor Cyan
Remove-Item -Path "docker\volumes\milvus\milvus\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "docker\volumes\milvus\etcd\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "docker\volumes\milvus\logs\*" -Recurse -Force -ErrorAction SilentlyContinue

# 清空 MinIO 数据
Write-Host "正在清空 MinIO 数据..." -ForegroundColor Cyan
Remove-Item -Path "docker\volumes\milvus\minio\*" -Recurse -Force -ErrorAction SilentlyContinue

# 清空应用数据
Write-Host "正在清空应用数据..." -ForegroundColor Cyan
Remove-Item -Path "saves\knowledge_base_data\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "saves\knowledge_graph\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "saves\tasks\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "saves\logs\*.log" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "数据清空完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "提示：请重新启动服务 (docker compose up -d)" -ForegroundColor Cyan