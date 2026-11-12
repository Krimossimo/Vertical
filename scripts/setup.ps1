# Installation automatique de Vertical (Windows 10/11)
# - vérifie ce qui est déjà présent avant d'installer quoi que ce soit
# - tout s'installe DANS le dossier de Vertical (aucun droit administrateur requis)
param(
    [switch]$CpuOnly,
    [switch]$SkipModels,
    [switch]$NoShortcut,
    [switch]$NoPause
)

# "Continue" : sous Windows PowerShell 5.1, "Stop" transforme la sortie stderr des outils en erreur fatale.
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
$Tools = Join-Path $Root "tools"
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
try { Start-Transcript -Path (Join-Path $Root "setup.log") -Append | Out-Null } catch {}

function Step($m) { Write-Host ""; Write-Host "==> $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "    [OK] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "    [!]  $m" -ForegroundColor Yellow }
function Info($m) { Write-Host "    $m" -ForegroundColor Gray }

function Download($url, $out) {
    Info "Téléchargement : $url"
    try {
        Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -ErrorAction Stop
    } catch {
        # repli : curl.exe (présent sur Windows 10+)
        & curl.exe -L --fail -o $out $url
        if ($LASTEXITCODE -ne 0) { throw "Téléchargement impossible : $url" }
    }
}

function Extract($zip, $dest) {
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & tar.exe -xf $zip -C $dest 2>$null
    if ($LASTEXITCODE -ne 0) { Expand-Archive -Path $zip -DestinationPath $dest -Force -ErrorAction Stop }
}

Write-Host ""
Write-Host "  V E R T I C A L  —  installation" -ForegroundColor Green
Write-Host "  Dossier : $Root"

# ------------------------------------------------------------------ 1. GPU
Step "Carte graphique"
$smi = (Get-Command nvidia-smi -ErrorAction SilentlyContinue)
$smiPath = if ($smi) { $smi.Source } elseif (Test-Path "$env:WINDIR\System32\nvidia-smi.exe") { "$env:WINDIR\System32\nvidia-smi.exe" } else { $null }
$HasNvidia = $false
if ($smiPath -and -not $CpuOnly) {
    try {
        $g = & $smiPath --query-gpu=name,driver_version,memory.total --format=csv,noheader
        Ok "GPU NVIDIA détecté : $g"
        $HasNvidia = $true
    } catch { Warn "nvidia-smi présent mais illisible : mode CPU" }
} else {
    Warn "Pas de GPU NVIDIA utilisable : Vertical fonctionnera sur CPU (plus lent)."
}

# ------------------------------------------------------------------ 2. FFmpeg
Step "FFmpeg"
$LocalFf = Join-Path $Tools "ffmpeg\bin\ffmpeg.exe"
$NeedFf = $true
if (Test-Path $LocalFf) {
    Ok "FFmpeg déjà installé dans Vertical"
    $NeedFf = $false
} else {
    $sys = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($sys) {
        $filters = (& $sys.Source -hide_banner -filters 2>$null) -join "`n"
        $encoders = (& $sys.Source -hide_banner -encoders 2>$null) -join "`n"
        if ($filters -match " subtitles " -and $encoders -match "libx264") {
            Ok "FFmpeg déjà présent sur le PC : $($sys.Source)"
            if ($encoders -notmatch "h264_nvenc") { Warn "Ce FFmpeg n'a pas NVENC : l'export utilisera le CPU." }
            $NeedFf = $false
        } else {
            Warn "Le FFmpeg du PC n'a pas libass/libx264 : installation d'une version complète dans Vertical."
        }
    } else {
        Info "FFmpeg absent : installation automatique (version portable, ~100 Mo)."
    }
}
if ($NeedFf) {
    $zip = Join-Path $env:TEMP "vertical-ffmpeg.zip"
    $tmp = Join-Path $Tools "_ffmpeg_tmp"
    try {
        Download "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" $zip
    } catch {
        Warn "gyan.dev indisponible, essai GitHub (BtbN)…"
        Download "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip" $zip
    }
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    Extract $zip $tmp
    $inner = Get-ChildItem $tmp -Directory | Select-Object -First 1
    $dest = Join-Path $Tools "ffmpeg"
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    Move-Item $inner.FullName $dest -ErrorAction Stop
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $zip -Force -ErrorAction SilentlyContinue
    if (Test-Path $LocalFf) { Ok "FFmpeg installé : $LocalFf" } else { throw "Installation de FFmpeg échouée." }
}

# ------------------------------------------------------------------ 3. uv (gestionnaire Python)
Step "Python (via uv)"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $Tools "python"
$env:UV_CACHE_DIR = Join-Path $Tools "uv-cache"
$env:UV_LINK_MODE = "hardlink"
$uv = $null
$localUv = Join-Path $Tools "uv\uv.exe"
if (Test-Path $localUv) { $uv = $localUv; Ok "uv déjà installé dans Vertical" }
else {
    $sysUv = Get-Command uv -ErrorAction SilentlyContinue
    if ($sysUv) { $uv = $sysUv.Source; Ok "uv déjà présent sur le PC : $uv" }
    else {
        Info "uv absent : installation portable (~20 Mo)."
        $zip = Join-Path $env:TEMP "vertical-uv.zip"
        Download "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip" $zip
        Extract $zip (Join-Path $Tools "uv")
        Remove-Item $zip -Force -ErrorAction SilentlyContinue
        $found = Get-ChildItem (Join-Path $Tools "uv") -Recurse -Filter uv.exe | Select-Object -First 1
        if ($found -and $found.FullName -ne $localUv) { Move-Item $found.FullName $localUv -Force }
        $uv = $localUv
        Ok "uv installé"
    }
}

$Venv = Join-Path $Root ".venv"
$Py = Join-Path $Venv "Scripts\python.exe"
if (Test-Path $Py) {
    Ok "Environnement Python existant : $(& $Py --version)"
} else {
    Info "Création de l'environnement Python 3.11 (Python est téléchargé par uv s'il manque)…"
    & $uv venv --python 3.11 $Venv
    if ($LASTEXITCODE -ne 0) { throw "Création de l'environnement Python échouée." }
    Ok "Environnement créé : $(& $Py --version)"
}

# ------------------------------------------------------------------ 4. dépendances
Step "Bibliothèques Python"
& $uv pip install --python $Py -r (Join-Path $Root "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Installation des dépendances échouée (voir setup.log)." }
Ok "Dépendances de base installées"

Step "PyTorch (IA image + son)"
$torchOk = $false
$needCuda = if ($HasNvidia) { "1" } else { "0" }
& $Py -c "import sys`ntry:`n import torch; sys.exit(0 if (torch.cuda.is_available() or '$needCuda'=='0') else 1)`nexcept Exception: sys.exit(1)"
if ($LASTEXITCODE -eq 0) {
    Ok "PyTorch déjà installé"
    $torchOk = $true
} else {
    if ($HasNvidia) {
        Info "Installation de PyTorch CUDA 12.4 (~2,5 Go, patience)…"
        & $uv pip install --python $Py torch --index-url https://download.pytorch.org/whl/cu124
    } else {
        Info "Installation de PyTorch CPU…"
        & $uv pip install --python $Py torch --index-url https://download.pytorch.org/whl/cpu
    }
    if ($LASTEXITCODE -eq 0) { $torchOk = $true; Ok "PyTorch installé" }
    else { Warn "PyTorch n'a pas pu être installé : Vertical utilisera l'analyse audio/vidéo classique (solution de secours)." }
}

# ------------------------------------------------------------------ 5. modèles
if (-not $SkipModels) {
    Step "Modèles IA locaux (téléchargés une seule fois, ~3 Go au total)"
    $env:PATH = (Join-Path $Tools "ffmpeg\bin") + ";" + $env:PATH
    & $Py (Join-Path $Root "scripts\prefetch.py") 2>&1 | ForEach-Object { "$_" } | Out-Host
    if ($LASTEXITCODE -ne 0) { Warn "Certains modèles seront téléchargés au premier lancement." }
}

# ------------------------------------------------------------------ 6. diagnostic
Step "Vérification"
$env:PATH = (Join-Path $Tools "ffmpeg\bin") + ";" + $env:PATH
& $Py -m vertical --check 2>&1 | ForEach-Object { "$_" } | Out-Host

# ------------------------------------------------------------------ 7. exécutable + raccourci
Step "Lanceur Vertical.exe"
$csc = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $csc)) { $csc = Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe" }
$exe = Join-Path $Root "Vertical.exe"
if (Test-Path $csc) {
    $ico = Join-Path $Root "assets\vertical.ico"
    & $csc /nologo /target:winexe /optimize+ "/out:$exe" "/win32icon:$ico" /r:System.Windows.Forms.dll (Join-Path $Root "scripts\launcher.cs") | Out-Host
    if (Test-Path $exe) { Ok "Vertical.exe créé" } else { Warn "Compilation du lanceur impossible : utilise « Lancer Vertical.bat »." }
} else {
    Warn ".NET Framework introuvable : utilise « Lancer Vertical.bat »."
}

if (-not $NoShortcut -and (Test-Path $exe)) {
    try {
        $desk = [Environment]::GetFolderPath("Desktop")
        $sh = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desk "Vertical.lnk"))
        $sh.TargetPath = $exe
        $sh.WorkingDirectory = $Root
        $sh.IconLocation = "$exe,0"
        $sh.Description = "Vertical — Shorts automatiques depuis tes VOD"
        $sh.Save()
        Ok "Raccourci « Vertical » ajouté sur le Bureau"
    } catch { Warn "Raccourci non créé : $_" }
}

# ------------------------------------------------------------------ 8. Ollama (optionnel)
$oll = Get-Command ollama -ErrorAction SilentlyContinue
if ($oll) { Ok "Ollama détecté : titres générés par IA locale disponibles (optionnel)." }
else { Info "Optionnel : installer Ollama (gratuit) puis « ollama pull qwen2.5:7b » pour des titres rédigés par IA locale." }

Write-Host ""
Write-Host "  Installation terminée. Lance Vertical avec Vertical.exe (ou le raccourci du Bureau)." -ForegroundColor Green
try { Stop-Transcript | Out-Null } catch {}
if (-not $NoPause) { Read-Host "Appuie sur Entrée pour fermer" }
