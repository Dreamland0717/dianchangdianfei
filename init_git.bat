@echo off
REM 电力消耗分析项目 Git 初始化脚本

echo 初始化 Git 仓库...
git init

echo 添加所有文件到暂存区...
git add .

echo 创建第一个提交...
git commit -m "Initial commit: 电力消耗分析项目"

echo.
echo Git 仓库已初始化，您可以手动添加远程仓库并推送代码:
echo 1. git remote add origin ^<your-repository-url^>
echo 2. git push -u origin master

pause