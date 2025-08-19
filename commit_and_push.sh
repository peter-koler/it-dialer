#!/bin/bash

# 自动提交代码到GitHub的脚本

echo "开始提交代码到GitHub..."

# 检查是否有未提交的更改
if [[ -z $(git status --porcelain) ]]; then
  echo "没有需要提交的更改"
  exit 0
fi

# 获取提交信息
read -p "请输入提交信息: " commit_message

# 如果没有输入提交信息，则使用默认信息
if [[ -z "$commit_message" ]]; then
  commit_message="Update code"
fi

# 添加所有更改到暂存区
echo "添加文件到暂存区..."
git add .

# 提交更改
echo "提交更改..."
git commit -m "$commit_message"

# 推送到远程仓库
echo "推送到GitHub..."
git push origin main

echo "代码已成功提交到GitHub!"