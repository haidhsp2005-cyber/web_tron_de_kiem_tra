# PowerShell script to run the exam mixing web application
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "              HỆ THỐNG TRỘN ĐỀ THI TRẮC NGHIỆM CHUẨN BỘ GD&ĐT" -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

$pythonCmd = "python"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $pythonCmd = "py"
    } elseif (Test-Path "C:\ProgramData\miniconda3\python.exe") {
        $pythonCmd = "C:\ProgramData\miniconda3\python.exe"
    } else {
        Write-Host "[LỖI] Không tìm thấy Python trên máy tính!" -ForegroundColor Red
        Write-Host "Vui lòng cài đặt Python từ https://www.python.org hoặc thêm Python vào PATH."
        Read-Host "Bấm Enter để thoát..."
        exit 1
    }
}

Write-Host "[*] Đang sử dụng Python: $pythonCmd" -ForegroundColor Green

# Tự động mở trình duyệt sau 2 giây
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8000"
} | Out-Null

Write-Host "[*] Đang khởi chạy máy chủ tại http://localhost:8000 ..." -ForegroundColor Cyan
Write-Host "[*] Trình duyệt web sẽ tự động mở sau 2 giây." -ForegroundColor Gray
Write-Host "[*] Để DỪNG máy chủ: Bấm tổ hợp phím Ctrl + C trong cửa sổ này." -ForegroundColor Yellow
Write-Host ""

& $pythonCmd app.py
