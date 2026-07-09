@echo off
chcp 65001 >nul
cd /d "C:\Users\Donaghy\Desktop\travel-recommender"
set PYTHONIOENCODING=utf-8
title 小比 AI 描述生成器
cls
echo ===============================================
echo   小比 AI 旅游目的地描述生成器  🐾
echo ===============================================
echo.
echo 开始时间：%date% %time%
echo.

:loop
echo [%time%] 启动批次...
python scripts\enrich_curl3.py
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% equ 3 (
    echo.
    echo ⚠ 遇到欠费错误！请充值后重新运行。
    pause
    exit /b 3
)

if exist data\enriched_ai_tmp.json (
    python -c "import json;d=json.load(open('data/enriched_ai_tmp.json',encoding='utf-8'));cnt=sum(1 for x in d['destinations'] if x.get('_d'));print(f'进度: {cnt}/{len(d[\"destinations\"])} 条');"
)

if %EXIT_CODE% equ 0 (
    echo.
    echo ✅ 全部 10,997 条目的地描述已生成！
    echo 输出文件: data\enriched_ai.json
    pause
    exit /b 0
)

echo [%time%] 批次完成，3秒后继续...
timeout /t 3 /nobreak >nul
goto loop
