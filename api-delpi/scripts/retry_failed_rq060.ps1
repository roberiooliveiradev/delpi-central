param([string]$Base = "X:\ENGENHARIA\1 LMP's\LMP 2026")
Add-Type -AssemblyName System.IO.Compression.FileSystem
function Get-DocxPlainText($Path) {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $reader = New-Object System.IO.StreamReader($zip.GetEntry('word/document.xml').Open())
        $xml = $reader.ReadToEnd(); $reader.Close()
        return ($xml -replace '<[^>]+>',' ' -replace '\s+',' ').Trim()
    } finally { $zip.Dispose() }
}
foreach ($num in @('010','026','033','047')) {
    $folder = Get-ChildItem -LiteralPath $Base -Directory | Where-Object { $_.Name -match "LMP\s*$num\s*26" } | Select-Object -First 1
    Write-Output "=== $num ==="
    if (-not $folder) { Write-Output "NOT_FOUND"; continue }
    Write-Output "FOLDER: $($folder.Name)"
    $rq = Get-ChildItem $folder.FullName -Recurse -Filter '*.docx' | Where-Object { $_.Name -match 'RQ-060|RQ060' } | Select-Object -First 1
    if (-not $rq) { Write-Output "NO_RQ"; continue }
    $t = Get-DocxPlainText $rq.FullName
    Write-Output "PREVIEW: $($t.Substring(0,[Math]::Min(300,$t.Length)))"
    if ($t -match 'OV\s*N.{0,3}:\s*(\d{6})') { Write-Output "OV=$($Matches[1])" }
    else {
        $m = [regex]::Match($t, '\b(\d{6})\b')
        if ($m.Success) { Write-Output "FALLBACK=$($m.Groups[1].Value)" }
    }
}
