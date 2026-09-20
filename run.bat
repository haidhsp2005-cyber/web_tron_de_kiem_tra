@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
title Hệ Thống Trộn Đề Thi Chuẩn Bộ GD&ĐT

echo ===============================================================================
echo                HỆ THỐNG TRỘN ĐỀ THI TRẮC NGHIỆM CHUẨN BỘ GD&ĐT
echo ===============================================================================
echo.

:: 1. Xác định trình thông dịch Python
set "PY_CMD="
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PY_CMD=py"
    ) else (
        if exist "C:\ProgramData\miniconda3\python.exe" (
            set "PY_CMD=C:\ProgramData\miniconda3\python.exe"
        ) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
            set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        ) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
            set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        ) else if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
            set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        )
    )
)

if "%PY_CMD%"=="" (
    echo [LỖI] Không tìm thấy Python trên máy tính của bạn!
    echo Vui lòng cài đặt Python từ https://www.python.org hoặc cài Miniconda.
    echo Nhớ tích chọn "Add Python to PATH" khi cài đặt.
    echo.
    pause
    exit /b 1
)

echo [*] Đang sử dụng Python: %PY_CMD%

:: 2. Kiểm tra các thư viện cần thiết
echo [*] Đang kiểm tra thư viện...
%PY_CMD% -c "import fastapi, uvicorn, docx, openpyxl, fitz, pypdf" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [*] Đang tự động cài đặt các thư viện cần thiết...
    %PY_CMD% -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [CẢNH BÁO] Cài đặt tự động gặp sự cố. Đang thử tiếp tục chạy...
    )
) else (
    echo [V] Các thư viện đã được cài đặt đầy đủ.
)

:: 3. Tự động mở trình duyệt web sau 2 giây
echo [*] Đang chuẩn bị mở trình duyệt tại http://localhost:8000 ...
start "" cmd /c "timeout /t 2 /nobreak > nul & start http://localhost:8000"

echo.
echo ===============================================================================
echo   MÁY CHỦ ĐANG CHẠY TẠI: http://localhost:8000
echo.
echo   * Cửa sổ trình duyệt web sẽ tự động mở sau 2 giây.
echo   * Bạn có thể thu nhỏ cửa sổ này nhưng ĐỪNG TẮT nó khi đang sử dụng.
echo   * Để DỪNG máy chủ: Bấm tổ hợp phím Ctrl + C hoặc đóng cửa sổ này.
echo ===============================================================================
echo.

:: 4. Chạy ứng dụng
%PY_CMD% app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LỖI] Ứng dụng đã dừng với mã lỗi %ERRORLEVEL%.
    pause
)
