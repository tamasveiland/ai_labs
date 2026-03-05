<#
.SYNOPSIS
    Enables local (key-based) authentication on the Azure Speech Service.

.DESCRIPTION
    Sets disableLocalAuth = false on the deployed Speech Service resource.
    This is required when Azure policy or a previous deployment has disabled
    key-based auth and you need it for local development.

    The script auto-discovers the resource name from the azd environment.
    You can also pass the resource group and name explicitly.

.PARAMETER ResourceGroupName
    Name of the resource group containing the Speech service.
    If omitted, read from azd env (AZURE_RESOURCE_GROUP).

.PARAMETER SpeechResourceName
    Name of the Speech service resource.
    If omitted, read from azd env (AZURE_SPEECH_RESOURCE_NAME).

.EXAMPLE
    .\scripts\Set-SpeechLocalAuth.ps1
    # Auto-discovers values from azd environment

.EXAMPLE
    .\scripts\Set-SpeechLocalAuth.ps1 -ResourceGroupName rg-speech-poc -SpeechResourceName speech-abc123
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$ResourceGroupName,

    [Parameter()]
    [string]$SpeechResourceName
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Step([string]$Message) {
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

# ── Resolve parameters from azd env if not provided ─────────────────────────
if (-not $ResourceGroupName) {
    Write-Step 'Reading AZURE_RESOURCE_GROUP from azd environment...'
    $ResourceGroupName = (azd env get-value AZURE_RESOURCE_GROUP 2>&1).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($ResourceGroupName)) {
        throw 'Could not resolve AZURE_RESOURCE_GROUP. Pass -ResourceGroupName or run from an azd-initialized folder.'
    }
}

if (-not $SpeechResourceName) {
    Write-Step 'Reading AZURE_SPEECH_RESOURCE_NAME from azd environment...'
    $SpeechResourceName = (azd env get-value AZURE_SPEECH_RESOURCE_NAME 2>&1).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($SpeechResourceName)) {
        throw 'Could not resolve AZURE_SPEECH_RESOURCE_NAME. Pass -SpeechResourceName or run from an azd-initialized folder.'
    }
}

Write-Step "Resource Group  : $ResourceGroupName"
Write-Step "Speech Resource : $SpeechResourceName"

# ── Check current state ─────────────────────────────────────────────────────
Write-Step 'Checking current disableLocalAuth value...'
$resourceId = az resource show `
    --resource-group $ResourceGroupName `
    --name $SpeechResourceName `
    --resource-type 'Microsoft.CognitiveServices/accounts' `
    --query 'id' `
    --output tsv

if ($LASTEXITCODE -ne 0) {
    throw "Failed to find Speech service '$SpeechResourceName' in resource group '$ResourceGroupName'."
}

$current = az resource show `
    --ids $resourceId `
    --query 'properties.disableLocalAuth' `
    --output tsv

Write-Host "    Current disableLocalAuth = $current"

if ($current -eq 'false' -or $current -eq 'False') {
    Write-Host "`nLocal auth is already enabled. No changes needed." -ForegroundColor Green
    return
}

# ── Update the resource ─────────────────────────────────────────────────────
Write-Step 'Setting disableLocalAuth = false ...'
az resource update `
    --ids $resourceId `
    --set properties.disableLocalAuth=false `
    --output none

if ($LASTEXITCODE -ne 0) {
    throw 'Failed to update disableLocalAuth on the Speech service.'
}

Write-Host "`nDone. Local (key-based) authentication is now enabled on '$SpeechResourceName'." -ForegroundColor Green
