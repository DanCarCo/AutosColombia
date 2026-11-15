# Verifica automáticamente lo comprobable de la entrega EA2. Ejecutar desde la raíz del repositorio:
#   .\entrega-ingenieria-software\verificar-entrega.ps1
# Parámetro -Rapido omite la compilación y las pruebas del frontend.
# No modifica archivos, no toca la base de datos y no hace commit.
param([switch]$Rapido)

$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent $PSScriptRoot
$resultados = New-Object System.Collections.Generic.List[object]

function Registrar([string]$nombre, [bool]$ok, [string]$detalle = '') {
    $resultados.Add([pscustomobject]@{ Comprobacion = $nombre; Estado = $(if ($ok) { 'OK' } else { 'FALLA' }); Detalle = $detalle })
}

Push-Location $raiz
try {
    # 1. Archivos de la entrega
    $archivos = @(
        'docs\01-requerimientos.md', 'docs\02-historias-de-usuario.md', 'docs\03-mockups-figma.md',
        'docs\04-diagramas.md', 'docs\05-plan-de-pruebas.md', 'docs\06-staruml.md',
        'entrega-ingenieria-software\staruml\AutosColombia.mdj',
        'entrega-ingenieria-software\diagramas\MF_AutosColombia.png'
    )
    $faltan = $archivos | Where-Object { -not (Test-Path $_) }
    Registrar 'A-G: documentos y diagramas presentes' ($faltan.Count -eq 0) ($faltan -join ', ')

    # 2. Modelo StarUML: JSON válido con Cliente y Pago
    try {
        $mdj = Get-Content 'entrega-ingenieria-software\staruml\AutosColombia.mdj' -Raw -Encoding UTF8
        $null = $mdj | ConvertFrom-Json
        $ok = ($mdj -match '"name": "Cliente"') -and ($mdj -match '"name": "Pago"') -and ($mdj -match 'CU-13 Validar mensualidad')
        Registrar 'StarUML: JSON válido con Cliente, Pago y CU-13' $ok
    } catch { Registrar 'StarUML: JSON válido' $false $_.Exception.Message }

    # 3. Secretos: ningún .env versionado
    $envs = git ls-files | Where-Object { $_ -match '(^|/)\.env$' }
    Registrar 'Sin .env versionado' (-not $envs) ($envs -join ', ')

    # 4. Backend
    Push-Location backend
    try {
        & .\.venv\Scripts\python.exe -m pip check | Out-Null
        Registrar 'Backend: pip check' ($LASTEXITCODE -eq 0)
        $sql = & .\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade 0003:0004 --sql 2>&1 | Out-String
        Registrar 'Migración 0004: CHECK modelo 1900-2200 (solo SQL, sin aplicar)' ($sql -match 'BETWEEN 1900 AND 2200')
        $salida = & .\.venv\Scripts\python.exe -m pytest -q 2>&1 | Out-String
        $resumen = ($salida -split "`n" | Where-Object { $_ -match 'passed|failed' } | Select-Object -Last 1).Trim()
        Registrar 'Backend: pytest' (($LASTEXITCODE -eq 0) -and ($salida -notmatch ' failed')) $resumen
    } finally { Pop-Location }

    # 5. Frontend
    if (-not $Rapido) {
        Push-Location frontend
        try {
            npm.cmd run build | Out-Null
            Registrar 'Frontend: compilación' ($LASTEXITCODE -eq 0)
            $salida = npm.cmd test -- --watch=false 2>&1 | Out-String
            $linea = [regex]::Replace((($salida -split "`n" | Where-Object { $_ -match 'Tests.*(passed|failed)' } | Select-Object -Last 1)), [string][char]27 + '\[[0-9;]*m', '')
            Registrar 'Frontend: pruebas' (($LASTEXITCODE -eq 0) -and ($salida -notmatch 'failed')) ("$linea").Trim()
        } finally { Pop-Location }
    }
} finally { Pop-Location }

$resultados | Format-Table -AutoSize -Wrap | Out-Host
$fallas = @($resultados | Where-Object { $_.Estado -eq 'FALLA' }).Count
if ($fallas -eq 0) { Write-Host 'Todo lo automático está en orden.' -ForegroundColor Green } else { Write-Host "$fallas comprobación(es) fallaron." -ForegroundColor Red; exit 1 }
Write-Host 'Pendiente de revisión humana: mockups en Figma, diagramas abiertos en StarUML, video en YouTube y URL del repositorio.'
