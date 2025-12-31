# Wikipedia Multistream Download Script
# Downloads all multistream XML files in controlled parallel batches

param(
    [int]$MaxParallel = 8
)

$baseUrl = "https://dumps.wikimedia.org/enwiki/20251220/"
$destDir = "c:\Coding\Self Reference Modeling\data\wikipedia\raw"

$files = @(
    "enwiki-20251220-pages-articles-multistream1.xml-p1p41242.bz2",
    "enwiki-20251220-pages-articles-multistream2.xml-p41243p151573.bz2",
    "enwiki-20251220-pages-articles-multistream3.xml-p151574p311329.bz2",
    "enwiki-20251220-pages-articles-multistream4.xml-p311330p558391.bz2",
    "enwiki-20251220-pages-articles-multistream5.xml-p558392p958045.bz2",
    "enwiki-20251220-pages-articles-multistream6.xml-p958046p1483661.bz2",
    "enwiki-20251220-pages-articles-multistream7.xml-p1483662p2134111.bz2",
    "enwiki-20251220-pages-articles-multistream8.xml-p2134112p2936260.bz2",
    "enwiki-20251220-pages-articles-multistream9.xml-p2936261p4045402.bz2",
    "enwiki-20251220-pages-articles-multistream10.xml-p4045403p5399366.bz2",
    "enwiki-20251220-pages-articles-multistream11.xml-p5399367p6899366.bz2",
    "enwiki-20251220-pages-articles-multistream11.xml-p6899367p7054859.bz2",
    "enwiki-20251220-pages-articles-multistream12.xml-p7054860p8554859.bz2",
    "enwiki-20251220-pages-articles-multistream12.xml-p8554860p9172788.bz2",
    "enwiki-20251220-pages-articles-multistream13.xml-p9172789p10672788.bz2",
    "enwiki-20251220-pages-articles-multistream13.xml-p10672789p11659682.bz2",
    "enwiki-20251220-pages-articles-multistream14.xml-p11659683p13159682.bz2",
    "enwiki-20251220-pages-articles-multistream14.xml-p13159683p14324602.bz2",
    "enwiki-20251220-pages-articles-multistream15.xml-p14324603p15824602.bz2",
    "enwiki-20251220-pages-articles-multistream15.xml-p15824603p17324602.bz2",
    "enwiki-20251220-pages-articles-multistream15.xml-p17324603p17460152.bz2",
    "enwiki-20251220-pages-articles-multistream16.xml-p17460153p18960152.bz2",
    "enwiki-20251220-pages-articles-multistream16.xml-p18960153p20460152.bz2",
    "enwiki-20251220-pages-articles-multistream16.xml-p20460153p20570392.bz2",
    "enwiki-20251220-pages-articles-multistream17.xml-p20570393p22070392.bz2",
    "enwiki-20251220-pages-articles-multistream17.xml-p22070393p23570392.bz2",
    "enwiki-20251220-pages-articles-multistream17.xml-p23570393p23716197.bz2",
    "enwiki-20251220-pages-articles-multistream18.xml-p23716198p25216197.bz2",
    "enwiki-20251220-pages-articles-multistream18.xml-p25216198p26716197.bz2",
    "enwiki-20251220-pages-articles-multistream18.xml-p26716198p27121850.bz2",
    "enwiki-20251220-pages-articles-multistream19.xml-p27121851p28621850.bz2",
    "enwiki-20251220-pages-articles-multistream19.xml-p28621851p30121850.bz2",
    "enwiki-20251220-pages-articles-multistream19.xml-p30121851p31308442.bz2",
    "enwiki-20251220-pages-articles-multistream20.xml-p31308443p32808442.bz2",
    "enwiki-20251220-pages-articles-multistream20.xml-p32808443p34308442.bz2",
    "enwiki-20251220-pages-articles-multistream20.xml-p34308443p35522432.bz2",
    "enwiki-20251220-pages-articles-multistream21.xml-p35522433p37022432.bz2",
    "enwiki-20251220-pages-articles-multistream21.xml-p37022433p38522432.bz2",
    "enwiki-20251220-pages-articles-multistream21.xml-p38522433p39996245.bz2",
    "enwiki-20251220-pages-articles-multistream22.xml-p39996246p41496245.bz2",
    "enwiki-20251220-pages-articles-multistream22.xml-p41496246p42996245.bz2",
    "enwiki-20251220-pages-articles-multistream22.xml-p42996246p44496245.bz2",
    "enwiki-20251220-pages-articles-multistream22.xml-p44496246p44788941.bz2",
    "enwiki-20251220-pages-articles-multistream23.xml-p44788942p46288941.bz2",
    "enwiki-20251220-pages-articles-multistream23.xml-p46288942p47788941.bz2",
    "enwiki-20251220-pages-articles-multistream23.xml-p47788942p49288941.bz2",
    "enwiki-20251220-pages-articles-multistream23.xml-p49288942p50564553.bz2",
    "enwiki-20251220-pages-articles-multistream24.xml-p50564554p52064553.bz2",
    "enwiki-20251220-pages-articles-multistream24.xml-p52064554p53564553.bz2",
    "enwiki-20251220-pages-articles-multistream24.xml-p53564554p55064553.bz2",
    "enwiki-20251220-pages-articles-multistream24.xml-p55064554p56564553.bz2",
    "enwiki-20251220-pages-articles-multistream24.xml-p56564554p57025655.bz2",
    "enwiki-20251220-pages-articles-multistream25.xml-p57025656p58525655.bz2",
    "enwiki-20251220-pages-articles-multistream25.xml-p58525656p60025655.bz2",
    "enwiki-20251220-pages-articles-multistream25.xml-p60025656p61525655.bz2",
    "enwiki-20251220-pages-articles-multistream25.xml-p61525656p62585850.bz2",
    "enwiki-20251220-pages-articles-multistream26.xml-p62585851p63975909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p63975910p65475909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p65475910p66975909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p66975910p68475909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p68475910p69975909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p69975910p71475909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p71475910p72975909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p72975910p74475909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p74475910p75975909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p75975910p77475909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p77475910p78975909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p78975910p80475909.bz2",
    "enwiki-20251220-pages-articles-multistream27.xml-p80475910p81895635.bz2",
    "enwiki-20251220-pages-articles-multistream-index.txt.bz2"
)

# Filter to files that don't exist yet
$toDownload = @()
foreach ($file in $files) {
    $dest = Join-Path $destDir $file
    if (-not (Test-Path $dest)) {
        $toDownload += $file
    }
}

if ($toDownload.Count -eq 0) {
    Write-Host "All files already downloaded!" -ForegroundColor Green
    exit 0
}

Write-Host "Downloading $($toDownload.Count) files with $MaxParallel parallel connections..."
Write-Host "Destination: $destDir"
Write-Host ""

# Process files in batches using background jobs
$completed = 0
$failed = @()
$startTime = Get-Date

for ($i = 0; $i -lt $toDownload.Count; $i += $MaxParallel) {
    $endIdx = [Math]::Min($i + $MaxParallel - 1, $toDownload.Count - 1)
    $batch = $toDownload[$i..$endIdx]
    $batchNum = [Math]::Floor($i / $MaxParallel) + 1
    $totalBatches = [Math]::Ceiling($toDownload.Count / $MaxParallel)
    
    Write-Host "Batch $batchNum/$totalBatches - Starting $($batch.Count) downloads..." -ForegroundColor Yellow
    
    $jobs = @()
    foreach ($file in $batch) {
        $url = "$baseUrl$file"
        $dest = Join-Path $destDir $file
        $job = Start-Job -ScriptBlock {
            param($u, $d, $f)
            try {
                $wc = New-Object System.Net.WebClient
                $wc.DownloadFile($u, $d)
                return @{OK = $true; Name = $f }
            }
            catch {
                return @{OK = $false; Name = $f; Err = $_.Exception.Message }
            }
        } -ArgumentList $url, $dest, $file
        $jobs += $job
    }
    
    # Wait for this batch
    $jobs | Wait-Job | Out-Null
    
    foreach ($job in $jobs) {
        $r = Receive-Job $job
        if ($r.OK) {
            $completed++
            Write-Host "  Done: $($r.Name)" -ForegroundColor Green
        }
        else {
            $failed += $r.Name
            Write-Host "  FAIL: $($r.Name) - $($r.Err)" -ForegroundColor Red
        }
        Remove-Job $job
    }
    
    $pct = [Math]::Round(($completed + $failed.Count) / $toDownload.Count * 100)
    Write-Host "  [$pct%] $completed done, $($failed.Count) failed, $($toDownload.Count - $completed - $failed.Count) remaining" -ForegroundColor Cyan
    Write-Host ""
}

$elapsed = (Get-Date) - $startTime
Write-Host "====================================="
Write-Host "COMPLETE in $($elapsed.ToString('hh\:mm\:ss'))"
Write-Host "  Success: $completed"
Write-Host "  Failed: $($failed.Count)"
Write-Host "====================================="

if ($failed.Count -gt 0) {
    Write-Host "Failed: $($failed -join ', ')" -ForegroundColor Red
    Write-Host "Re-run script to retry."
}
