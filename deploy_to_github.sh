#!/bin/bash

# 全量更新代码到 GitHub 的脚本

echo "开始全量更新代码到 GitHub..."

# 添加所有文件到暂存区（包括通常被忽略的文件，因为我们想要全量更新）
echo "添加所有文件到暂存区..."
git add --all

# 检查是否有需要提交的更改
if [[ -z $(git status --porcelain) ]]; then
  echo "没有需要提交的更改"
else
  # 提交更改
  echo "提交所有更改..."
  git commit -m "Full code update - $(date '+%Y-%m-%d %H:%M:%S')"
  
  # 检查提交是否成功
  if [ $? -ne 0 ]; then
    echo "提交失败！"
    exit 1
  fi
fi

# 强制推送所有更改到 GitHub（全量更新）
echo "强制推送所有代码到 GitHub..."
git push -u origin main --force

# 检查推送是否成功
if [ $? -ne 0 ]; then
  echo "推送失败！请检查您的网络连接和 Git 配置。"
  exit 1
else
  echo "代码已成功全量更新到 GitHub！"
fi