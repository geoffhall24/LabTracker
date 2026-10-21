@echo off
title HYDAC Automated Outlook Sync and GitHub Deploy
color 0A

set "PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files\Git\bin"

echo ============================================================
echo 1/3 Running Outlook Email Sync...
echo ============================================================
cd /d "C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker"
python sync_outlook.py

echo.
echo ============================================================
echo 2/3 Pulling Latest Online Changes from GitHub...
echo ============================================================
git pull origin main --rebase

echo.
echo ============================================================
echo 3/3 Pushing Updated Database to GitHub...
echo ============================================================
git add lab_queue.db
git commit -m "Auto-sync Outlook emails into database [%date% %time%]"
git push origin main

echo.
echo ============================================================
echo SUCCESS! Database updated locally and pushed to GitHub.
echo Streamlit Cloud will refresh in ~30 seconds.
echo ============================================================
pause