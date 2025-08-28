#!/bin/bash

# GitHub全量更新脚本
# 作者：灵码
# 版本：1.0

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # 无颜色

# 检查git是否安装
check_git() {
    if ! command -v git &> /dev/null; then
        echo -e "${RED}错误：git未安装，请先安装git${NC}"
        exit 1
    fi
}

# 初始化git仓库
init_git() {
    echo -e "${GREEN}正在初始化git仓库...${NC}"
    git init
    
    # 创建.gitignore文件
    cat > .gitignore << 'EOL'
# 忽略node_modules
node_modules/
# 忽略Python缓存
__pycache__/
*.pyc
*.pyo
*.pyd
# 忽略环境文件
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
# 忽略日志文件
*.log
# 忽略Docker相关
Dockerfile
.dockerignore
# 忽略IDE配置
.vscode/
.idea/
*.swp
*.swo
# 忽略构建目录
build/
dist/
*.pyc
*.db
*.sqlite3
# 忽略操作系统文件
.DS_Store
Thumbs.db
EOL
}

# 添加项目文件
add_project_files() {
    echo -e "${GREEN}正在添加项目文件...${NC}"
    
    # 添加所有项目文件
    git add .
    
    # 检查是否添加了关键文件
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误：添加文件失败，请检查.gitignore配置${NC}"
        exit 1
    fi
}

# 创建提交信息
create_commit() {
    echo -e "${GREEN}正在创建提交...${NC}"
    git commit -m "[自动化] 全量更新项目文件"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误：提交失败，可能没有需要提交的更改${NC}"
        exit 1
    fi
}

# 设置GitHub仓库地址
set_github_remote() {
    echo -e "${GREEN}请输入GitHub仓库地址 (HTTPS或SSH格式): ${NC}"
    read -r repo_url
    
    if [ -z "$repo_url" ]; then
        echo -e "${RED}错误：仓库地址不能为空${NC}"
        exit 1
    fi
    
    # 检测协议类型
    if [[ "$repo_url" == "git@"* ]]; then
        protocol="ssh"
    elif [[ "$repo_url" == "https:"* ]]; then
        protocol="https"
    else
        echo -e "${RED}错误：仅支持HTTPS或SSH协议的仓库地址${NC}"
        exit 1
    fi
    
    # 处理HTTPS协议
    if [ "$protocol" == "https" ]; then
        echo -e "${GREEN}请输入GitHub个人访问令牌(PAT): ${NC}"
        read -s -r token
        
        if [ -z "$token" ]; then
            echo -e "${RED}错误：令牌不能为空${NC}"
            exit 1
        fi
        
        # 替换URL中的密码部分
        repo_url="$(echo $repo_url | sed "s/https:\/\//https:\/\/$token@/")"
    fi
    
    # 移除现有origin（如果存在）
    git remote remove origin 2>/dev/null
    
    # 设置远程仓库
    git remote add origin "$repo_url"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误：设置远程仓库失败，请检查URL格式${NC}"
        exit 1
    fi
}

# 配置SSH密钥
configure_ssh() {
    echo -e "${GREEN}检测到SSH协议，正在配置SSH密钥...${NC}"
    
    # 检查SSH目录
    if [ ! -d "~/.ssh" ]; then
        mkdir -p ~/.ssh
        chmod 700 ~/.ssh
    fi
    
    # 检查是否存在SSH密钥
    if [ ! -f "~/.ssh/id_rsa.pub" ] && [ ! -f "~/.ssh/github.pub" ]; then
        echo -e "${GREEN}未检测到SSH密钥，正在生成新的SSH密钥...${NC}"
        ssh-keygen -t rsa -b 4096 -C "$(git config user.email)" -f ~/.ssh/github -N ""
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}错误：生成SSH密钥失败${NC}"
            exit 1
        fi
        
        echo -e "\n${GREEN}请将以下SSH公钥添加到GitHub账户:${NC}"
        cat ~/.ssh/github.pub
        echo -e "\nGitHub SSH密钥设置页面: https://github.com/settings/keys"
        
        # 添加SSH配置
        cat > ~/.ssh/config << 'EOL'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github
EOL
        chmod 600 ~/.ssh/config
    fi
    
    # 启动SSH代理
    eval $(ssh-agent) > /dev/null 2>&1
    ssh-add ~/.ssh/github > /dev/null 2>&1
}

# 推送到GitHub
push_to_github() {
    echo -e "${GREEN}正在推送到GitHub...${NC}"
    git push -u origin main --force
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误：推送失败，可能需要先创建仓库或检查权限${NC}"
        echo "请确保："
        echo "1. 仓库地址正确"
        echo "2. 您有写入权限"
        echo "3. 令牌/SSH密钥配置正确"
        exit 1
    fi
}

# 主函数
main() {
    echo -e "${GREEN}GitHub全量更新脚本开始执行${NC}"
    check_git
    
    # 检查是否已在git仓库中
    if [ -d .git ]; then
        echo "检测到现有git仓库"
        read -p "是否重新初始化仓库？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf .git
            init_git
        else
            echo "使用现有git仓库"
        fi
    else
        init_git
    fi
    
    add_project_files
    create_commit
    
    # 检测协议并配置认证
    if [ "$protocol" == "ssh" ]; then
        configure_ssh
    fi
    
    set_github_remote
    push_to_github
    
    echo -e "\n${GREEN}✅ 项目已成功推送到GitHub！${NC}"
    echo "当前分支：$(git rev-parse --abbrev-ref HEAD)"
    echo "远程仓库：$(git remote -v)"
    
    # 显示SSH密钥指纹（如果使用SSH）
    if [ "$protocol" == "ssh" ]; then
        echo -e "\n${GREEN}SSH密钥指纹：${NC}"
        ssh-keygen -l -f ~/.ssh/github.pub
    fi
}

# 执行主函数
main