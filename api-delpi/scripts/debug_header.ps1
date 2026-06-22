param([int]$N = 9)
Add-Type -AssemblyName System.IO.Compression.FileSystem
function Get-DocxPlainText($Path) {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $reader = New-Object System.IO.StreamReader($zip.GetEntry('word/document.xml').Open())
        $xml = $reader.ReadToEnd(); $reader.Close()
        return ($xml -replace '<[^>]+>',' ' -replace '\s+',' ').Trim()
    } finally { $zip.Dispose() }
}
$Base = "X:\ENGENHARIA\1 LMP's\LMP 2026"
$folder = Get-ChildItem -LiteralPath $Base -Directory | Where-Object { $_.Name -match ("LMP\s*0*{0}\s*26" -f $N) } | Select-Object -First 1
$rq = Get-ChildItem $folder.FullName -Recurse -Filter '*.docx' | Where-Object { $_.Name -match 'RQ-060|RQ060' } | Select-Object -First 1
$t = Get-DocxPlainText $rq.FullName
$clientIdx = $t.IndexOf('CLIENTE:')
$header = if ($clientIdx -gt 0) { $t.Substring(0, $clientIdx) } else { $t.Substring(0, [Math]::Min(600, $t.Length)) }
Write-Output "HEADER:"
Write-Output $header
Write-Output "---"
foreach ($m in [regex]::Matches($header, '\d{6}')) { Write-Output "6dig: $($m.Value)" }
foreach ($m in [regex]::Matches($header, 'N.{0,3}:\s*([^D]{0,30})')) { Write-Output "Nfield: $($m.Groups[1].Value)" }
