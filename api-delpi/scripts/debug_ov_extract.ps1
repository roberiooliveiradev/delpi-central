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
function Get-OvFromRqText($Text) {
    $m = [regex]::Match($Text, 'OV\s*N.{0,3}:\s*([\d\s]{2,14})', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if (-not $m.Success) { return $null }
    $compact = ($m.Groups[1].Value -replace '\s', '')
    $digitMatch = [regex]::Match($compact, '^\d{3,6}')
    if (-not $digitMatch.Success) { return $null }
    return $digitMatch.Value.PadLeft(6, '0')
}
foreach ($n in @(2,9,10,18,20,58)) {
    $folder = Get-ChildItem -LiteralPath $Base -Directory | Where-Object { $_.Name -match ("LMP\s*0*{0}\s*26" -f $n) } | Select-Object -First 1
    Write-Output "=== $n -> $($folder.Name) ==="
    $rq = Get-ChildItem $folder.FullName -Recurse -Filter '*.docx' | Where-Object { $_.Name -match 'RQ-060|RQ060' } | Select-Object -First 1
    $t = Get-DocxPlainText $rq.FullName
    $idx = $t.IndexOf('OV')
    Write-Output $t.Substring([Math]::Max(0,$idx), [Math]::Min(80, $t.Length-$idx))
    Write-Output "OV=$(Get-OvFromRqText $t)"
}
