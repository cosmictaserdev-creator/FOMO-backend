<#
.SYNOPSIS
  Assembles the full FOMO desktop bundle and compiles the Windows installer.

  Produces (in order):
    1. ktor-api's fat jar (./gradlew buildFatJar)
    2. a jlink'd minimal JRE for running that jar without a system Java install
    3. app/'s PyInstaller onedir build (the GUI + Python pipeline)
    4. one staged tree combining all three under installer\staging\
    5. FomoSetup.exe (Inno Setup) in installer\output\

  Run from anywhere; paths below are relative to this script's location.
#>
# Not "Stop": native tools (gradle/java/uv) routinely write benign chatter to stderr, and
# PowerShell 5.1 wraps that as a terminating NativeCommandError under $ErrorActionPreference
# = Stop even when the exe exits 0. Every native call below is checked via $LASTEXITCODE
# instead; ErrorActionPreference stays default so only real cmdlet errors (Copy-Item, etc.)
# stop the script.
$root = Split-Path -Parent $PSScriptRoot
if (-not $root) { $root = (Resolve-Path "$PSScriptRoot\..").Path }
$ktorDir = Join-Path $root "ktor-api"
$appDir = Join-Path $root "app"
$installerDir = Join-Path $root "installer"
$stagingDir = Join-Path $installerDir "staging"
$outputDir = Join-Path $installerDir "output"

Write-Host "== 1. Building Ktor fat jar ==" -ForegroundColor Cyan
Push-Location $ktorDir
& .\gradlew.bat buildFatJar --console=plain
if ($LASTEXITCODE -ne 0) { throw "gradlew buildFatJar failed" }
Pop-Location

$jarPath = Join-Path $ktorDir "build\libs\trend-hopper-api.jar"
if (-not (Test-Path $jarPath)) { throw "Expected fat jar not found: $jarPath" }

Write-Host "== 2. Building jlink runtime image ==" -ForegroundColor Cyan
$runtimeDir = Join-Path $ktorDir "runtime"
if (Test-Path $runtimeDir) { Remove-Item -Recurse -Force $runtimeDir }
$javaHome = $env:JAVA_HOME
if (-not $javaHome) { throw "JAVA_HOME must be set to a JDK 21+ install to run jlink" }
$jdeps = Join-Path $javaHome "bin\jdeps.exe"
$jlink = Join-Path $javaHome "bin\jlink.exe"
$modules = & $jdeps --print-module-deps --multi-release 23 --ignore-missing-deps $jarPath
Write-Host "jdeps-detected modules: $modules"
# jdk.crypto.ec/jdk.naming.dns are pulled in via SPI at runtime (TLS cipher suites, DNS)
# and jdeps' static analysis can't see them -- add explicitly rather than discovering
# the gap via a broken HTTPS handshake on a clean machine.
$allModules = "$modules,jdk.crypto.ec,jdk.naming.dns"
& $jlink --module-path "$javaHome\jmods" --add-modules $allModules --output $runtimeDir `
    --strip-debug --no-header-files --no-man-pages --compress=zip-6
if ($LASTEXITCODE -ne 0) { throw "jlink failed" }

Write-Host "== 3. Building PyInstaller onedir app ==" -ForegroundColor Cyan
Push-Location $appDir
uv run --group dev pyinstaller pyinstaller.spec --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }
Pop-Location

Write-Host "== 4. Staging bundle ==" -ForegroundColor Cyan
if (Test-Path $stagingDir) { Remove-Item -Recurse -Force $stagingDir }
New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null
Copy-Item -Recurse (Join-Path $appDir "dist\FomoControlPanel\*") $stagingDir
New-Item -ItemType Directory -Force -Path (Join-Path $stagingDir "jre") | Out-Null
Copy-Item -Recurse "$runtimeDir\*" (Join-Path $stagingDir "jre")
New-Item -ItemType Directory -Force -Path (Join-Path $stagingDir "ktor") | Out-Null
Copy-Item $jarPath (Join-Path $stagingDir "ktor")

Write-Host "== 5. Compiling installer ==" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$iscc = "C:\Program Files\Inno Setup 7\ISCC.exe"
if (-not (Test-Path $iscc)) { $iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" }
if (-not (Test-Path $iscc)) { throw "ISCC.exe not found -- install Inno Setup" }
& $iscc (Join-Path $installerDir "trendhopper.iss") "/O$outputDir"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup compile failed" }

Write-Host "Done. Installer at $outputDir\FomoSetup.exe" -ForegroundColor Green
