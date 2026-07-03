# ==============================================================================
# Restaurant Menu Sync Script
#
# Detects connected USB drives labeled "SCREEN-1" and "SCREEN-2", pulls the latest
# menus from the local cloned repository, finds the highest version menu file,
# archives old menu files on the USB drives, and copies the newest version.
# ==============================================================================

# --- Configuration ---
# Use the directory where the script is located as the repository path
$RepoPath = $PSScriptRoot
$Mappings = @{
    "SCREEN-1" = "base/screen1"
    "SCREEN-2" = "base/screen2"
}

# --- 1. Update Repository ---
Write-Host "Updating local repository from GitHub..." -ForegroundColor Cyan
if (Test-Path $RepoPath) {
    $prevLocation = Get-Location
    Set-Location $RepoPath
    try {
        git pull
    } catch {
        Write-Warning "Failed to run 'git pull'. Proceeding with currently local files."
    }
    Set-Location $prevLocation
} else {
    Write-Warning "Local repository not found at '$RepoPath'. Please ensure the repo is cloned."
}

# --- 2. Detect Connected USB Drives ---
Write-Host "Checking for connected menu USB drives..." -ForegroundColor Cyan
$volumes = Get-Volume | Where-Object { $_.FileSystemLabel -in $Mappings.Keys }

if (-not $volumes) {
    Write-Host "No connected menu screen USB drives (SCREEN-1, SCREEN-2) detected." -ForegroundColor Yellow
    return
}

# --- 3. Process Each USB Drive ---
foreach ($vol in $volumes) {
    $label = $vol.FileSystemLabel
    $driveLetter = "$($vol.DriveLetter):"
    
    if ([string]::IsNullOrEmpty($vol.DriveLetter)) {
        Write-Warning "Drive for '$label' does not have an assigned letter. Skipping."
        continue
    }

    Write-Host "`n--------------------------------------------------" -ForegroundColor Gray
    Write-Host "Processing Drive: $driveLetter ($label)" -ForegroundColor Green
    Write-Host "--------------------------------------------------" -ForegroundColor Gray

    # Determine source directory in repository
    $subFolder = $Mappings[$label]
    $sourceDir = Join-Path $RepoPath $subFolder
    
    if (-not (Test-Path $sourceDir)) {
        Write-Warning "Source directory not found in repository: $sourceDir"
        continue
    }

    # Find menu images with version pattern (e.g., screen1-v11.png)
    $files = Get-ChildItem -Path $sourceDir -File | Where-Object { $_.Name -match '-v(\d+)\.[^.]+$' }
    if (-not $files) {
        Write-Warning "No versioned menu files (*-v*.png) found in: $sourceDir"
        continue
    }

    # Sort descending by version number parsed as integer and select the newest
    $newestFile = $files | Sort-Object {
        if ($_.Name -match '-v(\d+)\.[^.]+$') {
            [int]$Matches[1]
        } else {
            0
        }
    } -Descending | Select-Object -First 1

    Write-Host "Newest menu version found: $($newestFile.Name)" -ForegroundColor Cyan

    $targetRoot = "$driveLetter\"
    $targetFile = Join-Path $targetRoot $newestFile.Name
    $archiveDir = Join-Path $targetRoot "archive"

    # Ensure archive folder exists on the USB drive
    if (-not (Test-Path $archiveDir)) {
        Write-Host "Creating archive folder on $driveLetter..." -ForegroundColor Gray
        New-Item -ItemType Directory -Path $archiveDir | Out-Null
    }

    # Find existing menu files in root that need archiving
    # Excluding the archive folder itself, hidden/system files, and shortcuts
    $existingFiles = Get-ChildItem -Path $targetRoot -File | Where-Object {
        $_.Name -ne $newestFile.Name -and 
        $_.Attributes -notlike "*Hidden*" -and 
        $_.Attributes -notlike "*System*" -and
        $_.Extension -ne ".lnk" -and
        $_.Extension -ne ".url"
    }

    if ($existingFiles) {
        Write-Host "Archiving old menu files..." -ForegroundColor Yellow
        foreach ($file in $existingFiles) {
            $archiveDest = Join-Path $archiveDir $file.Name
            
            # Avoid name collisions in the archive directory
            $counter = 1
            $fileNameWithoutExt = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
            $ext = $file.Extension
            while (Test-Path $archiveDest) {
                $archiveDest = Join-Path $archiveDir "$fileNameWithoutExt`_$counter$ext"
                $counter++
            }
            
            Write-Host "  -> Moving $($file.Name) to archive as $(Split-Path $archiveDest -Leaf)" -ForegroundColor Gray
            try {
                Move-Item -Path $file.FullName -Destination $archiveDest -Force
            } catch {
                Write-Error "Failed to archive $($file.Name): $_"
            }
        }
    }

    # Copy the new menu file to the root of the USB drive if it's not already there
    if (-not (Test-Path $targetFile)) {
        Write-Host "Copying latest menu ($($newestFile.Name)) to root..." -ForegroundColor Cyan
        try {
            Copy-Item -Path $newestFile.FullName -Destination $targetFile -Force
            Write-Host "Successfully updated $label with $($newestFile.Name)!" -ForegroundColor Green
        } catch {
            Write-Error "Failed to copy $($newestFile.Name) to USB drive root: $_"
        }
    } else {
        Write-Host "Drive is already up-to-date with $($newestFile.Name)." -ForegroundColor Green
    }
}

Write-Host "`nSync operation completed!" -ForegroundColor Green
