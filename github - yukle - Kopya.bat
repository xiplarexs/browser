@echo off
setlocal EnableDelayedExpansion

:: ==========================================
::   SABIT AYARLAR - sadece burasi degistir
:: ==========================================
set "GITHUB_USER=xiplarexs"
set "GITHUB_TOKEN=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"
:: ==========================================

cd /d "%~dp0"

:: Klasor adini al
for %%F in ("%~dp0.") do set "RAW_NAME=%%~nxF"

:: Bosluk varsa tire ile degistir (URL icin guvenli)
set "REPO_NAME=%RAW_NAME: =-%"

set "REMOTE_URL=https://%GITHUB_TOKEN%@github.com/%GITHUB_USER%/%REPO_NAME%.git"

echo.
echo ==========================================
echo   XipSoft GitHub Yedekleme
echo   Kullanici : %GITHUB_USER%
echo   Repo      : %REPO_NAME%
echo ==========================================
echo.

echo [1/6] Git deposu kontrol ediliyor...
if not exist .git (
    git init >nul 2>&1
    echo [OK] Git deposu baslatildi
) else (
    echo [OK] Mevcut depo kullaniliyor
)
git remote remove origin >nul 2>&1
git remote add origin "%REMOTE_URL%" >nul 2>&1

echo [2/6] Git kimligi ayarlaniyor...
git config user.email "%GITHUB_USER%@users.noreply.github.com" >nul
git config user.name "%GITHUB_USER%" >nul
echo [OK] %GITHUB_USER%

if not exist ".gitignore" (
    echo [!] .gitignore olusturuluyor...
    (
        echo .xipsoft_config
        echo *.env
        echo .env
        echo .env.local
        echo node_modules/
        echo .wwebjs_auth/
        echo .wwebjs_cache/
        echo *.log
        echo results.json
        echo .DS_Store
        echo Thumbs.db
        echo desktop.ini
    ) > .gitignore
    echo [OK] .gitignore olusturuldu
)

echo [3/6] Dosyalar ekleniyor...
git add -A
echo [OK] Tum dosyalar eklendi

echo [4/6] Commit olusturuluyor...
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set "dt=%%I"
set "CDATE=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%"
set "CTIME=%dt:~8,2%:%dt:~10,2%"
git commit -m "Yedekleme: %CDATE% %CTIME% [%REPO_NAME%]" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Commit: %CDATE% %CTIME%
) else (
    echo [~] Degisiklik yok, commit atildi
)

echo [5/6] Branch ve uzak repo kontrol ediliyor...
git branch -M main >nul 2>&1
git ls-remote origin >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Repo yok, GitHub'da olusturuluyor...
    curl -s -X POST ^
        -H "Authorization: token %GITHUB_TOKEN%" ^
        -H "Content-Type: application/json" ^
        -d "{\"name\":\"%REPO_NAME%\",\"private\":true,\"description\":\"XipSoft Backup\"}" ^
        "https://api.github.com/user/repos" >nul 2>&1
    echo [OK] Private repo olusturuldu: %REPO_NAME%
    echo [OK] Ilk push yapiliyor...
    git push -u origin main
    goto :done
)

git pull origin main --allow-unrelated-histories --no-rebase --no-edit >nul 2>&1

echo [6/6] GitHub'a yukleniyor...
git push -u origin main

:done
echo.
if %errorlevel% equ 0 (
    echo ==========================================
    echo   BASARILI: github.com/%GITHUB_USER%/%REPO_NAME%
    echo ==========================================
) else (
    echo ==========================================
    echo   HATA: Asagidakileri kontrol et
    echo   1. Token gecerli mi?
    echo   2. Token repo yetkisi var mi?
    echo   github.com/settings/tokens
    echo ==========================================
)
echo.
pause
