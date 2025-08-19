#!/bin/bash

# 自动提交代码到GitHub的脚本（增强版）

echo "开始提交代码到GitHub..."

# 检查是否有未提交的更改
if [[ -z $(git status --porcelain) ]]; then
  echo "没有需要提交的更改"
  # 自动拉取最新代码
  echo "正在同步远程仓库的更新..."
  git pull origin main
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

# 先尝试拉取远程更改以避免冲突
echo "正在同步远程仓库的更新..."
git pull origin main

# 检查拉取操作是否成功
if [ $? -ne 0 ]; then
  echo ""
  echo "自动合并失败！可能有冲突需要手动解决。"
  echo "请手动运行以下命令解决冲突："
  echo "  git pull origin main"
  echo "解决冲突后，再运行此脚本。"
  echo ""
  # 撤销提交，保留更改在工作区
  git reset --soft HEAD~1
  exit 1
fi

# 推送到远程仓库
echo "推送到GitHub..."
git push origin main

# 检查推送操作是否成功
if [ $? -ne 0 ]; then
  echo ""
  echo "推送失败！"
  echo "请检查您的网络连接和Git配置。"
  echo ""
else
  echo "代码已成功提交到GitHub!"
fi