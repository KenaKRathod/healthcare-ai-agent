$nodeModules = Join-Path $PSScriptRoot "node_modules\.bin\vite.cmd"
Write-Host "Starting Vite dev server..."
& $nodeModules
