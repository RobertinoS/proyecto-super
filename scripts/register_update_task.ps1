param(
    [string]$TaskName = "ProyectoSuperActualizacion",
    [string]$StartTime = "07:00",
    [int]$RepeatHours = 5
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$UpdateScript = Join-Path $ProjectRoot "run_update.bat"

if (-not (Test-Path $UpdateScript)) {
    throw "No se encontro run_update.bat en $ProjectRoot"
}

$taskCommand = "`"$UpdateScript`""
$args = @(
    "/Create",
    "/TN", $TaskName,
    "/TR", $taskCommand,
    "/SC", "HOURLY",
    "/MO", $RepeatHours,
    "/ST", $StartTime,
    "/F"
)

$result = Start-Process -FilePath "schtasks.exe" -ArgumentList $args -NoNewWindow -Wait -PassThru
if ($result.ExitCode -ne 0) {
    throw "No se pudo registrar la tarea. Codigo de salida: $($result.ExitCode)"
}

Write-Host "Tarea programada registrada: $TaskName"
Write-Host "Primer inicio: $StartTime"
Write-Host "Repeticion: cada $RepeatHours horas"
