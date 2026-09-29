$desktop = [System.Environment]::GetFolderPath('Desktop')
$wsh = New-Object -ComObject WScript.Shell
$projectDir = (Get-Location).Path

$targetExe = Join-Path $projectDir "dist\WebGIS_Angra.exe"
$iconPath = Join-Path $projectDir "app_icon.ico"
$shortcutPath = Join-Path $desktop "WebGIS Angra dos Reis.lnk"

$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetExe
$shortcut.WorkingDirectory = (Join-Path $projectDir "dist")
$shortcut.Description = "Sistema WebGIS MOVMASSA - Angra dos Reis"
if (Test-Path $iconPath) {
    $shortcut.IconLocation = "$iconPath,0"
}
$shortcut.Save()

Write-Output "Atalho criado com sucesso na Area de Trabalho: $shortcutPath"
