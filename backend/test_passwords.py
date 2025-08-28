#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models.user import User

app = create_app()
app.app_context().push()

# 测试用户密码
users_to_test = ['test', 'superadmin']
passwords_to_test = ['123456', 'test', 'superadmin', 'password', 'admin']

for username in users_to_test:
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"\n用户 {username}:")
        print(f"  状态: {user.status}")
        print(f"  角色: {user.role}")
        print(f"  密码哈希: {user.password_hash}")
        
        for password in passwords_to_test:
            result = user.check_password(password)
            print(f"  密码 '{password}': {'✅' if result else '❌'}")
    else:
        print(f"用户 {username} 不存在")