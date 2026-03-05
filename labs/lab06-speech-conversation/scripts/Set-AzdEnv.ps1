<#
.SYNOPSIS
    Initialises the azd environment for Lab06: Speech Conversation.

.DESCRIPTION
    Sets required azd environment variables (AZURE_LOCATION, etc.) that are
    needed before running 'azd up' or 'azd provision'.

    Subscription-scoped Bicep deployments require AZURE_LOCATION to tell ARM
    where to store the deployment metadata.  This script ensures it is set.

.PARAMETER Location
    Azure region for the deployment (default: swedencentral).

.PARAMETER EnvironmentName
    Name of the azd environment. If omitted, uses the current default environment.

.EXAMPLE
    .\scripts\Set-AzdEnv.ps1
    # Uses defaults (swedencentral, current azd environment)

.EXAMPLE
    .\scripts\Set-AzdEnv.ps1 -Location eastus2
    # Sets AZURE_LOCATION to eastus2
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$Location = 'swedencentral',

    [Parameter()]
    [string]$EnvironmentName
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── helpers ──────────────────────────────────────────────────────────────────
function Write-Step([string]$Message) {
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

# ── resolve environment ──────────────────────────────────────────────────────
if ($EnvironmentName) {
    Write-Step "Selecting azd environment: $EnvironmentName"
    azd env select $EnvironmentName
    if ($LASTEXITCODE -ne 0) { throw "Failed to select azd environment '$EnvironmentName'." }
}

# ── set AZURE_LOCATION ──────────────────────────────────────────────────────
Write-Step "Setting AZURE_LOCATION = $Location"
azd env set AZURE_LOCATION $Location
if ($LASTEXITCODE -ne 0) { throw 'Failed to set AZURE_LOCATION.' }

# ── verify ───────────────────────────────────────────────────────────────────
Write-Step 'Current azd environment values:'
azd env get-values

Write-Host "`nDone. You can now run 'azd up' or 'azd provision'." -ForegroundColor Green
