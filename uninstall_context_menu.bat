@echo off
echo Uninstalling context menu...

reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.mp3\shell\GenerateLRC" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.wav\shell\GenerateLRC" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.m4a\shell\GenerateLRC" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.flac\shell\GenerateLRC" /f >nul 2>&1

echo Done! Context menu removed.
pause
