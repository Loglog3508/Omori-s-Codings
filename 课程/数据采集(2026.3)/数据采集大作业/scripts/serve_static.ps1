param(
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$listener = [System.Net.HttpListener]::new()
$prefix = "http://localhost:$Port/"
$listener.Prefixes.Add($prefix)
$listener.Start()
Write-Host "Serving $root at $prefix"

$mime = @{
  ".html" = "text/html; charset=utf-8"
  ".css" = "text/css; charset=utf-8"
  ".js" = "application/javascript; charset=utf-8"
  ".json" = "application/json; charset=utf-8"
  ".png" = "image/png"
  ".jpg" = "image/jpeg"
  ".jpeg" = "image/jpeg"
  ".svg" = "image/svg+xml"
}

while ($listener.IsListening) {
  $context = $listener.GetContext()
  try {
    $path = [Uri]::UnescapeDataString($context.Request.Url.AbsolutePath.TrimStart("/"))
    if ([string]::IsNullOrWhiteSpace($path)) {
      $path = "frontend/index.html"
    }
    if ($path.EndsWith("/")) {
      $path = "$path/index.html"
    }
    $fullPath = [System.IO.Path]::GetFullPath((Join-Path $root $path))
    if (-not $fullPath.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
      $context.Response.StatusCode = 403
      $context.Response.Close()
      continue
    }
    if (-not [System.IO.File]::Exists($fullPath)) {
      $context.Response.StatusCode = 404
      $bytes = [System.Text.Encoding]::UTF8.GetBytes("Not found")
      $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
      $context.Response.Close()
      continue
    }
    $extension = [System.IO.Path]::GetExtension($fullPath).ToLowerInvariant()
    $context.Response.ContentType = if ($mime.ContainsKey($extension)) { $mime[$extension] } else { "application/octet-stream" }
    $bytes = [System.IO.File]::ReadAllBytes($fullPath)
    $context.Response.ContentLength64 = $bytes.Length
    $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $context.Response.Close()
  } catch {
    $context.Response.StatusCode = 500
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($_.Exception.Message)
    $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $context.Response.Close()
  }
}
