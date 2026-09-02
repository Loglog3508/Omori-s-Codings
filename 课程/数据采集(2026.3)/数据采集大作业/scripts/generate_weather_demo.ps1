$ErrorActionPreference = "Stop"

$scriptPath = $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($scriptPath)) {
  $root = (Get-Location).Path
} else {
  $root = Split-Path -Parent (Split-Path -Parent $scriptPath)
}

$dataDir = Join-Path $root "data"
$frontendDataDir = Join-Path (Join-Path $root "frontend") "data"
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
New-Item -ItemType Directory -Force -Path $frontendDataDir | Out-Null

$end = (Get-Date).Date.AddDays(-7)
$start = $end.AddYears(-10).AddDays(1)
$rows = New-Object System.Collections.Generic.List[object]
$daily = @{
  time = New-Object System.Collections.Generic.List[string]
  weather_code = New-Object System.Collections.Generic.List[int]
  temperature_2m_max = New-Object System.Collections.Generic.List[double]
  temperature_2m_min = New-Object System.Collections.Generic.List[double]
  temperature_2m_mean = New-Object System.Collections.Generic.List[double]
  apparent_temperature_max = New-Object System.Collections.Generic.List[double]
  apparent_temperature_min = New-Object System.Collections.Generic.List[double]
  precipitation_sum = New-Object System.Collections.Generic.List[double]
  rain_sum = New-Object System.Collections.Generic.List[double]
  snowfall_sum = New-Object System.Collections.Generic.List[double]
  precipitation_hours = New-Object System.Collections.Generic.List[double]
  wind_speed_10m_max = New-Object System.Collections.Generic.List[double]
  wind_gusts_10m_max = New-Object System.Collections.Generic.List[double]
  shortwave_radiation_sum = New-Object System.Collections.Generic.List[double]
}

function Get-Season([int]$month) {
  if ($month -in 3,4,5) { return "春季" }
  if ($month -in 6,7,8) { return "夏季" }
  if ($month -in 9,10,11) { return "秋季" }
  return "冬季"
}

function Get-WeatherText([int]$code) {
  switch ($code) {
    0 { "晴" }
    1 { "多云" }
    2 { "多云" }
    3 { "阴" }
    45 { "雾" }
    61 { "小雨" }
    63 { "中雨" }
    65 { "大雨" }
    71 { "小雪" }
    73 { "中雪" }
    80 { "阵雨" }
    default { "其他" }
  }
}

for ($d = $start; $d -le $end; $d = $d.AddDays(1)) {
  $dayOfYear = $d.DayOfYear
  $yearOffset = $d.Year - $start.Year
  $seasonWave = [math]::Sin((2 * [math]::PI * ($dayOfYear - 172)) / 365)
  $trend = $yearOffset * 0.035
  $mean = [math]::Round(12.2 + 13.5 * $seasonWave + $trend + [math]::Sin($dayOfYear * 0.43) * 1.4, 2)
  $range = 5.5 + [math]::Abs([math]::Sin($dayOfYear * 0.21)) * 4.2
  $tmax = [math]::Round($mean + $range / 2, 2)
  $tmin = [math]::Round($mean - $range / 2, 2)
  $rainSignal = [math]::Sin(($dayOfYear - 125) / 365 * 2 * [math]::PI)
  $wet = (($dayOfYear * 17 + $d.Year) % 9) -lt 3
  $heavy = (($dayOfYear * 31 + $d.Year) % 91) -eq 0
  $precip = 0.0
  if ($wet) { $precip = [math]::Round([math]::Max(0.2, 2.2 + 8.5 * [math]::Max(0, $rainSignal) + (($dayOfYear * 7) % 6)), 2) }
  if ($heavy) { $precip += 25.0 }
  $snow = 0.0
  if ($d.Month -in 12,1,2 -and $wet) { $snow = [math]::Round($precip * 0.55, 2) }
  $wind = [math]::Round(16 + [math]::Abs([math]::Sin($dayOfYear * 0.11)) * 24 + (($dayOfYear * 5) % 8), 2)
  $gust = [math]::Round($wind + 8 + (($dayOfYear * 3) % 12), 2)
  $radiation = [math]::Round(9 + 11 * [math]::Max(0, $seasonWave) + (($dayOfYear * 13) % 4), 2)
  $code = 0
  if ($precip -gt 25) { $code = 65 }
  elseif ($snow -gt 0) { $code = 71 }
  elseif ($precip -gt 8) { $code = 63 }
  elseif ($precip -gt 0) { $code = 61 }
  elseif (($dayOfYear + $d.Year) % 11 -eq 0) { $code = 45 }
  elseif (($dayOfYear + $d.Year) % 4 -eq 0) { $code = 3 }
  elseif (($dayOfYear + $d.Year) % 3 -eq 0) { $code = 2 }
  else { $code = 0 }

  $daily.time.Add($d.ToString("yyyy-MM-dd"))
  $daily.weather_code.Add($code)
  $daily.temperature_2m_max.Add($tmax)
  $daily.temperature_2m_min.Add($tmin)
  $daily.temperature_2m_mean.Add($mean)
  $daily.apparent_temperature_max.Add([math]::Round($tmax + 0.8, 2))
  $daily.apparent_temperature_min.Add([math]::Round($tmin - 1.1, 2))
  $daily.precipitation_sum.Add($precip)
  $daily.rain_sum.Add([math]::Max(0, $precip - $snow))
  $daily.snowfall_sum.Add($snow)
  $daily.precipitation_hours.Add($(if ($precip -gt 0) { [math]::Round(1 + (($dayOfYear * 7) % 10), 2) } else { 0.0 }))
  $daily.wind_speed_10m_max.Add($wind)
  $daily.wind_gusts_10m_max.Add($gust)
  $daily.shortwave_radiation_sum.Add($radiation)

  $rows.Add([ordered]@{
    date = $d.ToString("yyyy-MM-dd")
    year = $d.Year
    month = $d.Month
    season = Get-Season $d.Month
    weather_code = $code
    weather_text = Get-WeatherText $code
    temp_max = $tmax
    temp_min = $tmin
    temp_mean = $mean
    temp_range = [math]::Round($tmax - $tmin, 2)
    apparent_max = [math]::Round($tmax + 0.8, 2)
    apparent_min = [math]::Round($tmin - 1.1, 2)
    precipitation = $precip
    rain = [math]::Max(0, $precip - $snow)
    snowfall = $snow
    precipitation_hours = $(if ($precip -gt 0) { [math]::Round(1 + (($dayOfYear * 7) % 10), 2) } else { 0.0 })
    wind_max = $wind
    wind_gust = $gust
    radiation = $radiation
    is_hot = $tmax -ge 30
    is_cold = $tmin -le -5
    is_rainy = $precip -ge 0.1
    is_heavy_rain = $precip -ge 25
    is_snowy = $snow -gt 0
    is_windy = $wind -ge 38
    source = "demo-weather"
  })
}

$yearGroups = $rows | Group-Object year
$yearly = foreach ($g in $yearGroups) {
  [ordered]@{
    year = [int]$g.Name
    avg_temp = [math]::Round((($g.Group | Measure-Object temp_mean -Average).Average), 2)
    precipitation = [math]::Round((($g.Group | Measure-Object precipitation -Sum).Sum), 2)
    hot_days = @($g.Group | Where-Object { $_.is_hot }).Count
    cold_days = @($g.Group | Where-Object { $_.is_cold }).Count
    rainy_days = @($g.Group | Where-Object { $_.is_rainy }).Count
  }
}

$monthGroups = $rows | Group-Object { "{0}-{1:D2}" -f $_.year, $_.month }
$monthly = foreach ($g in $monthGroups) {
  [ordered]@{
    month = $g.Name
    avg_temp = [math]::Round((($g.Group | Measure-Object temp_mean -Average).Average), 2)
    precipitation = [math]::Round((($g.Group | Measure-Object precipitation -Sum).Sum), 2)
    days = $g.Count
  }
}

$weatherCounts = $rows | Group-Object weather_text | Sort-Object Count -Descending | ForEach-Object {
  [ordered]@{ name = $_.Name; value = $_.Count }
}

$raw = [ordered]@{
  latitude = 38.914
  longitude = 121.6147
  timezone = "Asia/Shanghai"
  daily = $daily
  location = @{ name = "大连市"; latitude = 38.914; longitude = 121.6147; timezone = "Asia/Shanghai" }
  source = "demo-weather"
  source_url = ""
}

$meta = [ordered]@{
  generated_at = (Get-Date).ToString("s")
  topic = "大连市近10年天气数据分析"
  location = @{ name = "大连市"; latitude = 38.914; longitude = 121.6147; timezone = "Asia/Shanghai" }
  source = "demo-weather"
  source_url = ""
  total_days = $rows.Count
  date_start = $rows[0].date
  date_end = $rows[$rows.Count - 1].date
  avg_temp = [math]::Round((($rows | Measure-Object temp_mean -Average).Average), 2)
  max_temp = (($rows | Measure-Object temp_max -Maximum).Maximum)
  min_temp = (($rows | Measure-Object temp_min -Minimum).Minimum)
  total_precipitation = [math]::Round((($rows | Measure-Object precipitation -Sum).Sum), 2)
  rainy_days = @($rows | Where-Object { $_.is_rainy }).Count
  hot_days = @($rows | Where-Object { $_.is_hot }).Count
  cold_days = @($rows | Where-Object { $_.is_cold }).Count
  yearly = $yearly
  monthly = $monthly
  weather_counts = $weatherCounts
  note = "当前环境网络采集失败时使用结构一致的本地演示天气数据；真实采集成功后 source 会显示 open-meteo。"
}

$rawJson = $raw | ConvertTo-Json -Depth 8
$cleanJson = $rows | ConvertTo-Json -Depth 8
$metaJson = $meta | ConvertTo-Json -Depth 8
$dataScript = "window.WEATHER_DATA = $cleanJson;`nwindow.WEATHER_META = $metaJson;`n"

$rawJson | Set-Content -Path (Join-Path $dataDir "weather_raw.json") -Encoding UTF8
$cleanJson | Set-Content -Path (Join-Path $dataDir "weather_clean.json") -Encoding UTF8
$metaJson | Set-Content -Path (Join-Path $dataDir "weather_metadata.json") -Encoding UTF8
$dataScript | Set-Content -Path (Join-Path $dataDir "weather_data.js") -Encoding UTF8
$cleanJson | Set-Content -Path (Join-Path $frontendDataDir "weather_clean.json") -Encoding UTF8
$metaJson | Set-Content -Path (Join-Path $frontendDataDir "weather_metadata.json") -Encoding UTF8
$dataScript | Set-Content -Path (Join-Path $frontendDataDir "weather_data.js") -Encoding UTF8

Write-Host "Generated $($rows.Count) demo weather records."
