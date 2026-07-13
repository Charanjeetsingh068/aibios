# AI-BOS Enterprise Local Setup Script (Windows PowerShell)
# ==============================================================================

$ErrorActionPreference = "Stop"

# Helper for colored output
function Write-Header {
    param([string]$text)
    Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$text)
    Write-Host "  [PASS] $text" -ForegroundColor Green
}

function Write-Warning {
    param([string]$text)
    Write-Host "  [WARN] $text" -ForegroundColor Yellow
}

function Write-Failure {
    param([string]$text)
    Write-Host "  [FAIL] $text" -ForegroundColor Red
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AI-BOS Enterprise Local Setup & Environment Builder    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# ------------------------------------------------------------------------------
# 1. Verify Basic CLI Tools
# ------------------------------------------------------------------------------
Write-Header "Verifying CLI Tool Prerequisites"

# Verify Python
try {
    $pythonVersionStr = python --version 2>&1
    if ($pythonVersionStr -match "Python\s+(\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Failure "Python version must be >= 3.10. Found: $pythonVersionStr"
            Exit 1
        }
        Write-Success "Python installation: $pythonVersionStr"
    } else {
        Write-Warning "Could not parse Python version string: $pythonVersionStr"
    }
} catch {
    Write-Failure "Python is not installed or not in the system PATH. Please install Python 3.10+."
    Exit 1
}

# Verify Node.js
try {
    $nodeVersion = node --version
    if ($nodeVersion -match "v(\d+)") {
        $nodeMajor = [int]$Matches[1]
        if ($nodeMajor -lt 18) {
            Write-Failure "Node.js version must be >= 18.0.0. Found: $nodeVersion"
            Exit 1
        }
        Write-Success "Node.js installation: $nodeVersion"
    } else {
        Write-Warning "Could not parse Node.js version string: $nodeVersion"
    }
} catch {
    Write-Failure "Node.js is not installed or not in the system PATH. Please install Node.js >= 18.0.0."
    Exit 1
}

# Verify npm
try {
    $npmVersion = npm --version
    Write-Success "npm installation: v$npmVersion"
} catch {
    Write-Failure "npm is not installed or not in the PATH."
    Exit 1
}

# ------------------------------------------------------------------------------
# 2. Setup Configuration Files (.env)
# ------------------------------------------------------------------------------
Write-Header "Generating Environment Configurations"

$envFiles = @(
    @{ Path = ".env"; Example = ".env.example" },
    @{ Path = "backend/.env"; Example = "backend/.env.example" },
    @{ Path = "frontend/.env"; Example = "frontend/.env.example" },
    @{ Path = "mobile/.env"; Example = "mobile/.env.example" }
)

foreach ($item in $envFiles) {
    if (-not (Test-Path $item.Path)) {
        if (Test-Path $item.Example) {
            Copy-Item $item.Example $item.Path
            Write-Success "Created configuration file: $($item.Path)"
        } else {
            Write-Warning "Configuration template missing: $($item.Example)"
        }
    } else {
        Write-Host "  [SKIP] Configuration file already exists: $($item.Path)" -ForegroundColor Gray
    }
}

# ------------------------------------------------------------------------------
# 3. Setup Python Virtual Environment and Backend Dependencies
# ------------------------------------------------------------------------------
Write-Header "Setting Up Python Virtual Environment (Backend)"

$backendDir = Resolve-Path "./backend"
$venvPath = Join-Path $backendDir ".venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating Virtual Environment at $venvPath..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Success "Created python virtual environment."
} else {
    Write-Host "  [SKIP] Virtual environment already exists at $venvPath" -ForegroundColor Gray
}

Write-Host "Installing/Upgrading dependencies inside virtual environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\pip" install --upgrade pip
& "$venvPath\Scripts\pip" install -r "$backendDir\requirements.txt"
Write-Success "Backend dependencies installed successfully."

# ------------------------------------------------------------------------------
# 4. Setup Node.js Dependencies (Frontend & Mobile)
# ------------------------------------------------------------------------------
Write-Header "Installing Node.js Package Dependencies"

# Frontend Next.js dependencies
$frontendDir = Resolve-Path "./frontend"
if (Test-Path $frontendDir) {
    Write-Host "Installing frontend console packages (Next.js)..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
    Write-Success "Frontend console packages installed."
}

# Mobile companion app dependencies
$mobileDir = Resolve-Path "./mobile"
if (Test-Path $mobileDir) {
    Write-Host "Installing mobile companion packages (React Native)..." -ForegroundColor Yellow
    Push-Location $mobileDir
    npm install
    Pop-Location
    Write-Success "Mobile companion packages installed."
}

# ------------------------------------------------------------------------------
# 5. Verify Local Database Dependencies Connectivity
# ------------------------------------------------------------------------------
Write-Header "Verifying Database Connection Ports (Local)"

$databases = @(
    @{ Name = "PostgreSQL"; Port = 5432 },
    @{ Name = "MongoDB"; Port = 27017 },
    @{ Name = "Redis"; Port = 6379 }
)

$dbFailures = 0

function Test-DatabasePort {
    param([string]$name, [int]$port)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $connection = $client.BeginConnect("127.0.0.1", $port, $null, $null)
        $success = $connection.AsyncWaitHandle.WaitOne(1500)
        if ($success) {
            $client.EndConnect($connection)
            Write-Success "$name is online and listening on port $port."
            return $true
        } else {
            Write-Failure "$name is unreachable on port $port."
            return $false
        }
    } catch {
        Write-Failure "$name connection failed: $_"
        return $false
    } finally {
        $client.Close()
    }
}

foreach ($db in $databases) {
    $result = Test-DatabasePort -name $db.Name -port $db.Port
    if (-not $result) {
        $dbFailures++
    }
}

# ------------------------------------------------------------------------------
# Success / Status Report
# ------------------------------------------------------------------------------
Write-Host "`n==========================================================" -ForegroundColor Cyan
if ($dbFailures -eq 0) {
    Write-Host "   AI-BOS Setup Successful! All components are ready.      " -ForegroundColor Green
} else {
    Write-Host "   AI-BOS Setup Incomplete: $dbFailures database service(s) offline.  " -ForegroundColor Yellow
    Write-Host "   Please ensure PostgreSQL (5432), MongoDB (27017), and Redis (6379)" -ForegroundColor Yellow
    Write-Host "   are running locally on your system." -ForegroundColor Yellow
}
Write-Host "   To run verification check, execute: npm run verify     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
