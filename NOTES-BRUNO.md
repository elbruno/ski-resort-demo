# Bruno Notes — Aspire local Azure provisioning

Quick runbook to fix the Aspire **"can pick tenant but subscription is empty"** issue on a new machine.

## Preconditions

- Azure CLI installed
- Aspire CLI installed
- **Go installed** (required by `datagenerator` — see step 0 below)
- Logged into Azure
- You have permission on the target subscription

## 0) Install Go if missing (required for datagenerator)

`datagenerator` runs `go mod tidy` at startup; if Go is not in PATH it will `FailedToStart`
and cascade-block all agents (they all end up `Waiting`).

Check first:

```powershell
go version
```

If missing, install via winget (requires admin) or portable (no admin needed):

**Via winget (recommended if you have admin):**

```powershell
winget install --id GoLang.Go -e --accept-package-agreements --accept-source-agreements
# restart terminal after install
```

**Portable (no admin required):**

```powershell
$goVersion = '1.26.4'
$zipUrl = "https://go.dev/dl/go$goVersion.windows-amd64.zip"
$targetRoot = Join-Path $env:USERPROFILE 'tools'
$zipPath = Join-Path $targetRoot "go$goVersion.windows-amd64.zip"
$extractPath = Join-Path $targetRoot "go$goVersion"
New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
$goBin = Join-Path $extractPath 'go\bin'

# Add to permanent user PATH
$currentPath = [System.Environment]::GetEnvironmentVariable('PATH','User')
[System.Environment]::SetEnvironmentVariable('PATH', "$goBin;$currentPath", 'User')
$env:PATH = "$goBin;$env:PATH"
go version
```

After installing Go, restart Aspire (`aspire stop; aspire start --non-interactive`).

## 1) Sign in and validate subscription (CLI context)

```powershell
az login
az account list --all --output table
az account set --subscription "efd2f794-f20f-4476-9220-8ee76c0a9279"
az account show
```

Expected subscription used in this repo:

- Subscription: `dotnet`
- Subscription ID: `efd2f794-f20f-4476-9220-8ee76c0a9279`
- Tenant ID: `a0eaf323-ba84-4da5-96f1-a110978978f2` (CoreAI DevRel 2608)
- Location: `swedencentral`

## 2) Set Aspire local provisioning secrets (required)

Run from the AppHost folder:

```powershell
cd src
aspire secret set "Azure:SubscriptionId" "efd2f794-f20f-4476-9220-8ee76c0a9279"
aspire secret set "Azure:Location" "swedencentral"
aspire secret set "Azure:TenantId" "a0eaf323-ba84-4da5-96f1-a110978978f2"
```

Optional sanity check:

```powershell
aspire secret list
```

## 3) Start Aspire

```powershell
aspire start --non-interactive
```

If you run from VS/VS Code Run button and get the Azure provisioning popup again, close it and relaunch after secrets are set.

## 4) If subscription dropdown is still empty

This is usually auth-context mismatch (IDE Azure account context != Azure CLI context).

Do these in order:

1. In VS Code Azure account UI, switch to tenant `CoreAI DevRel 2608`.
2. Ensure subscription `dotnet` is selected.
3. Reload VS Code window.
4. Retry Aspire run.

## 5) Strong fallback (force Aspire to use Azure CLI auth)

If the UI context is still flaky, force credential source:

```powershell
cd src
aspire secret set "Azure:CredentialSource" "AzureCli"
```

Then restart Aspire.

## 6) Useful checks

```powershell
# Confirm region is valid
az account list-locations --query "[?name=='swedencentral'].[name,displayName]" -o table

# Confirm current Azure account context
az account show
```

## Notes

- Aspire local provisioning requires `Azure:SubscriptionId` and `Azure:Location`.
- Adding `Azure:TenantId` helps avoid tenant mismatch on multi-tenant accounts.
- Keep secrets in Aspire user-secrets (not committed appsettings values).
