param(
    [string]$Base = "X:\ENGENHARIA\1 LMP's\LMP 2026",
    [int]$StartNum = 2,
    [int]$EndNum = 98
)

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-DocxPlainText {
    param([string]$Path)
    $zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $entry = $zip.GetEntry('word/document.xml')
        if (-not $entry) { return '' }
        $reader = New-Object System.IO.StreamReader($entry.Open())
        try {
            $xml = $reader.ReadToEnd()
        } finally {
            $reader.Close()
        }
        return ($xml -replace '<w:tab[^>]*/>', ' ' `
                     -replace '</w:p>', ' ' `
                     -replace '<[^>]+>', '' `
                     -replace '&amp;', '&' `
                     -replace '&lt;', '<' `
                     -replace '&gt;', '>' `
                     -replace '\s+', ' ').Trim()
    } finally {
        $zip.Dispose()
    }
}

function Get-OvFromRqText {
    param([string]$Text)
    $clientIdx = $Text.IndexOf('CLIENTE:')
    $header = if ($clientIdx -gt 0) { $Text.Substring(0, $clientIdx) } else { $Text.Substring(0, [Math]::Min(700, $Text.Length)) }

    # 1) seis dígitos contíguos no cabeçalho (ex.: 003386, 003443)
    $six = [regex]::Match($header, '\d{6}')
    if ($six.Success) { return $six.Value }

    # 2) último campo "Nº:" com dígitos espaçados (ex.: 003 532)
    $nFields = [regex]::Matches($header, 'N.{0,3}:\s*([\d\sFORMTEXT]{2,24})')
    if ($nFields.Count -gt 0) {
        $raw = ($nFields[$nFields.Count - 1].Groups[1].Value -replace 'FORMTEXT|FORMCHECKBOX', '' -replace '\s', '')
        if ($raw -match '^\d{3,6}$' -and $raw -notmatch '^\d{1,3}26$') {
            return $raw.PadLeft(6, '0')
        }
    }

    # 3) campo "OV Nº:" com dígitos incompletos/espaçados (ex.: 00 352, 00 5)
    $ovField = [regex]::Match($header, 'OV\s*N.{0,3}:\s*([\d\s]{2,10})')
    if ($ovField.Success) {
        $raw = ($ovField.Groups[1].Value -replace 'FORMTEXT|FORMCHECKBOX', '' -replace '\s', '')
        if ($raw -match '^\d{3,6}$') { return $raw.PadLeft(6, '0') }
    }

    return $null
}

function Get-MonthFromNum {
    param([int]$Num)
    if ($Num -le 10) { return '2026-01' }
    if ($Num -le 36) { return '2026-02' }
    if ($Num -le 53) { return '2026-03' }
    if ($Num -le 69) { return '2026-04' }
    if ($Num -le 86) { return '2026-05' }
    return '2026-06'
}

$results = @()
for ($n = $StartNum; $n -le $EndNum; $n++) {
    $code = '{0:D3} 26' -f $n
    $num = '{0:D3}' -f $n
    $month = Get-MonthFromNum -Num $n

    $folder = Get-ChildItem -LiteralPath $Base -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match ("LMP\s*0*{0}\s*26" -f $n) } |
        Select-Object -First 1

    if (-not $folder) {
        $results += [pscustomobject]@{
            lmp_num = $n
            lmp_ano = $code
            mes = $month
            folder = $null
            rq060 = $null
            ov = $null
            error = 'pasta_nao_encontrada'
        }
        continue
    }

    $rqFiles = Get-ChildItem -LiteralPath $folder.FullName -Recurse -File -Filter '*.docx' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match 'RQ-060|RQ060|Análise Crítica|Analise Critica|ANÁLISE CRÍTICA|ANALISE CRITICA' }

    if (-not $rqFiles -or $rqFiles.Count -eq 0) {
        $results += [pscustomobject]@{
            lmp_num = $n
            lmp_ano = $code
            mes = $month
            folder = $folder.Name
            rq060 = $null
            ov = $null
            error = 'rq060_nao_encontrado'
        }
        continue
    }

    $rq = $rqFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $text = Get-DocxPlainText -Path $rq.FullName
    $ov = Get-OvFromRqText -Text $text

    $results += [pscustomobject]@{
        lmp_num = $n
        lmp_ano = $code
        mes = $month
        folder = $folder.Name
        rq060 = $rq.FullName
        ov = $ov
        error = if ($ov) { $null } else { 'ov_nao_extraida' }
    }
}

$results | ConvertTo-Json -Depth 5
