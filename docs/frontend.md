# 前端邮箱验证功能

> 2026-05-26

## 一、流程概述

```
注册 → 发送验证邮件 → 邮箱验证 → 登录
```

1. 用户在登录页注册账号
2. 后端发送验证邮件（含 JWT token 链接）
3. 用户点击邮件中的链接跳转到 `/verify-email?token=xxx`
4. 验证成功后跳转登录页，验证失败可重新发送验证邮件
5. 登录时若邮箱未验证，弹出对话框支持重新发送

## 二、涉及文件

| 文件 | 说明 |
| :--- | :--- |
| `src/types/user.ts` | `VerifyEmailData`、`ResendVerifyRequest` 类型定义 |
| `src/api/auth.ts` | `verifyEmail(token)`、`resendVerification(email)` API 方法 |
| `src/views/auth/VerifyEmailView.vue` | 验证邮箱页面，处理三种状态 |
| `src/views/auth/LoginView.vue` | 注册成功提示 + 登录未验证弹窗 |
| `src/router/index.ts` | `/verify-email` 路由 |

## 三、API 接口

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/verify-email` | 验证邮箱，body: `{ token }` |
| `POST` | `/api/v1/auth/resend-verification` | 重新发送验证邮件，body: `{ email }` |

## 四、VerifyEmailView 状态处理

| 状态 | token | 展示 |
| :--- | :--- | :--- |
| 加载中 | 有效 | 旋转图标 + "正在验证邮箱..." |
| 成功 | 有效 | 绿色勾 + "邮箱验证成功" + 去登录按钮 |
| 链接无效 | 缺失/无效 | 警告图标 + 重新发送表单 |
| 链接过期 | 过期 | 警告图标 + "验证链接已过期" + 重新发送表单 |
| 已验证 | 重复使用 | 警告图标 + "邮箱已验证" |

## 五、登录页增强

- **注册成功**：提示 "注册成功！验证邮件已发送至您的邮箱，请查收"
- **登录被拒**：后端返回 `Email not verified` 时，弹出对话框支持输入邮箱重新发送验证邮件
