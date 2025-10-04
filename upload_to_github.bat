@echo off
cd /d "%~dp0"

REM إعداد اسم المستخدم والبريد الإلكتروني
git config --global user.name "azzaz1782-ship-it"
git config --global user.email "azzaz1782@gmail.com"

REM تهيئة المستودع وربطه
git init
git add .
git commit -m "Auto upload via script"
git branch -M main
git remote remove origin
git remote add origin https://github.com/azzaz1782-ship-it/telegram-bot-railway.git

REM رفع المشروع إلى GitHub
git push -u origin main
