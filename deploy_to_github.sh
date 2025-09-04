#!/bin/bash

# 全量更新代码到 GitHub 的脚本（真正意义上的全量覆盖）

echo "开始全量更新代码到 GitHub..."

# 备份当前的 .gitignore 文件
echo "备份当前的 .gitignore 文件..."
cp .gitignore .gitignore.bak

# 临时清空 .gitignore 文件，确保所有文件都会被添加
echo "临时移除 .gitignore 限制..."
> .gitignore

# 添加所有文件到暂存区（现在不会有任何文件被忽略）
echo "添加所有文件到暂存区..."
git add --all

# 恢复 .gitignore 文件
echo "恢复 .gitignore 文件..."
mv .gitignore.bak .gitignore

# 提交所有更改
echo "提交所有更改..."
git commit -m "Full code update - $(date '+%Y-%m-%d %H:%M:%S')"

# 检查提交是否成功
if [ $? -ne 0 ]; then
  echo "提交失败！"
  exit 1
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