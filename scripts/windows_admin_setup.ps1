# Prepares a Windows machine for running the Book 1 notebooks locally (REPRODUCE.md, section 1).
# Run once as administrator, from your own account (UAC), e.g.:
#   Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File scripts\windows_admin_setup.ps1'
#
#   1. folders/files that upstream notebooks hardcode as absolute paths, writable by $User
#   2. command-line tools notebooks call with "!": wget, unzip, Graphviz (dot)
param([string]$User = $env:USERNAME)
$ErrorActionPreference = "Stop"
$home_dir = "C:\Users\$User"

# --- 1. Hardcoded paths (REPRODUCE.md 4.16, 4.17) ---------------------------------------------
$dirs = @(
    "C:\Users\kpmurphy\github\bookv2\figures",                      # /Users/kpmurphy/...: gaussEvec, seq_logo_demo, ...
    "C:\teamspace\studios\this_studio\pyprobml\notebooks\figures"   # /teamspace/...: linreg_poly_vs_degree
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force $d | Out-Null
    Write-Host "created $d"
}
icacls "C:\Users\kpmurphy" /grant "${User}:(OI)(CI)M" /T | Out-Null
icacls "C:\teamspace" /grant "${User}:(OI)(CI)M" /T | Out-Null

# (pcaImageDemo's savefig("/PcaTrainFaceImages.png") is redirected by tests/test_notebooks.py instead)

# --- 2. Command-line tools (REPRODUCE.md 4.23) -------------------------------------------------
# wget: ae_mnist_conv, vae_mnist_conv_lightning, matrix_factorization_recommender
winget install --id JernejSimoncic.Wget -e --source winget --accept-package-agreements --accept-source-agreements
# Graphviz (dot): hbayes_maml
winget install --id Graphviz.Graphviz -e --source winget --accept-package-agreements --accept-source-agreements

# unzip: matrix_factorization_recommender. Wrapper around the unzip.exe that ships with Git
# (copying the exe alone would not work: it needs the msys DLLs next to it).
$bin = "$home_dir\bin"
New-Item -ItemType Directory -Force $bin | Out-Null
Set-Content "$bin\unzip.cmd" '@"C:\Program Files\Git\usr\bin\unzip.exe" %*' -Encoding ascii
icacls $bin /grant "${User}:(OI)(CI)M" | Out-Null
Write-Host "created $bin\unzip.cmd"

# Add Graphviz and the bin folder to the user's PATH (HKCU of $User, not of an admin account)
$sid = (New-Object Security.Principal.NTAccount($User)).Translate([Security.Principal.SecurityIdentifier]).Value
$key = "Registry::HKEY_USERS\$sid\Environment"
$path = (Get-ItemProperty $key -Name Path -ErrorAction SilentlyContinue).Path
foreach ($p in "C:\Program Files\Graphviz\bin", $bin) {
    if (($path -split ";") -notcontains $p) { $path = ($path.TrimEnd(";") + ";" + $p).TrimStart(";") }
}
Set-ItemProperty $key -Name Path -Value $path -Type ExpandString
Write-Host "user PATH now ends with: $(($path -split ';' | Select-Object -Last 3) -join ';')"

Write-Host "`nDone. Open a new terminal (or restart Claude Code) so the updated PATH is used. Press Enter to close."
Read-Host | Out-Null
