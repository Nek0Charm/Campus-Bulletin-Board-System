# Campus Bulletin Board System 开发规范

> 

## 一、项目概述

| 项目信息 | 详情 |
| :------- | :--- |
| 名称 | Campus Bulletin Board System (校园论坛) |
| 仓库 | https://github.com/Nek0Charm/Campus-Bulletin-Board-System- |
| 描述 | 一个面向大学校园的在线论坛系统，提供用户注册、发帖、评论、点赞等功能|


## 二、技术栈

### 2.1 前端技术

React or Vue，未定，但需使用 typescript 开发，并用 pnpm 管理

### 2.2 后端技术

#### 核心技术栈

| 技术       | 说明      |
| :--------- | --------- |
| Python     | 编程语言  |
| FastAPI    | 框架      |
| PostgreSQL | 主数据库  |
| Redis      | 缓存/会话 |
| pwdlib     | 密码加密  |
| SQLAlchemy | ORM       |
| pydantic   |数据校验  |
| PyJWT      | 认证鉴权  |

#### 工程管理与测试

| 技术                        | 说明       |
| --------------------------- | ----------|
| black                       | 代码格式化 |
| ruff                        | 静态检查   |
| pytest+pytest-asyncio+httpx | 测试框架   |
| uv                          | 项目管理   |


### 2.3 开发工具

| 工具       | 说明       |
| :--------- | ---------- |
| Git        | 版本控制   |
| Docker Compose | 容器化部署 |
| Husky      | Git hooks  |


## 三、项目结构

待定

## 四、Git 规范

### 4.1 分支结构
```plaintext
main                        # 生产环境（受保护）
│
├── develop                 # 开发主分支（受保护）
│   │        
│   └──feat/xxx      # 功能分支
│      ├── fix/xxx       # 修复分支
│      └── refactor/xxx  # 重构分支
└── docs/xxx                # 文档分支
```

### 4.2 分支保护

|分支|规则|
|:--|:--|
|main|受保护，由组长从 develop 分支定期合并|
|develop|受保护，提交 pull request 后组长审核通过才能合并|
|feat/*|各组员自行管理，建议定期与 develop 同步|

### 4.3 分支命名

| 类型 | 格式                              | 示例                       |
| ---- | --------------------------------- | -------------------------- |
| 功能 | `feat/<子系统>-<功能>-<日期>`     | `feat/user-crud-0401`    |
| 修复 | `fix/<子系统>-<描述>-<日期>`      | `fix/user-login-error-0401`   |
| 重构 | `refactor/<子系统>-<描述>-<日期>` | `refactor/user-logout-0401` |
| 文档 | `docs/<描述>-<日期>`              | `docs/api-spec-0401`       |

> 不强制要求完全符合上述格式 
### 4.4 Commit 规范

**格式**:
```plaintext
<type>(<scope>): <subject>
```
**类型（Type）：**

| 类型       | 说明               | 示例                               |
| ---------- | ------------------ | ---------------------------------- |
| `feat`     | 新功能             | `feat(user): add user CRUD API`       |
| `fix`      | Bug 修复           | `fix(user): resolve login issue`      |
| `refactor` | 重构（不增加功能） | `refactor(board): optimize scheduler`  |
| `docs`     | 文档更新           | `docs: update API specification`   |
| `test`     | 测试               | `test(store): add unit tests`          |
| `chore`    | 构建/工具          | `chore(deps): update dependencies` |

### 4.5 工作流程

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feat/user-crud-0401

# 2. 开发并提交
git add .
git commit -m "feat(user): add user CRUD API"
git push origin feat/user-crud-0401

# 3. 合并到 develop（所有组员）
git checkout develop
git merge feat/user-crud-0401 --no-ff
git push origin develop

# 5. develop → main（组长协商后执行）
```

## 五、API 规范

### 5.1 RESTful 规范

| 方法     | 路径                | 说明         |
| -------- | ------------------- | ------------ |
| `GET`    | `/api/v1/users`     | 获取用户列表 |
| `GET`    | `/api/v1/users/:id` | 获取单个用户 |
| `POST`   | `/api/v1/users`     | 创建用户     |
| `PATCH`  | `/api/v1/users/:id` | 部分更新用户 |
| `DELETE` | `/api/v1/users/:id` | 删除用户     |


### 5.2 响应格式


**成功响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

**分页响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  },
  "request_id": "abc123"
}
```

**错误响应：**

```json
{
  "code": 40001,
  "message": "参数校验失败",
  "errors": [{ "field": "username", "message": "用户名不能为空" }],
  "request_id": "abc123"
}
```

> **注**：`request_id` 用于请求追踪，可选字段。

### 5.3 HTTP 状态码


| 状态码 | 说明               |
| ------ | ------------------ |
| 200    | 成功               |
| 201    | 创建成功           |
| 204    | 删除成功（无返回） |
| 400    | 参数错误           |
| 401    | 未认证             |
| 403    | 无权限             |
| 404    | 资源不存在         |
| 409    | 资源冲突           |
| 422    | 业务规则不满足     |
| 429    | 请求过于频繁       |
| 500    | 服务器内部错误     |


## 六、代码规范

### 6.1 Python 代码规范

遵循 **PEP 8**，并以 `black + ruff` 作为统一标准：

- 统一使用 `uvx black` 格式化。
- 提交前必须通过 `uvx ruff check`
- `import` 分组顺序：标准库 → 第三方库 → 项目内模块。

**命名规范：**

| 对象 | 规范 | 示例 |
| :-- | :-- | :-- |
| 变量/函数 | `snake_case` | `create_user` |
| 类/异常 | `PascalCase` | `UserService` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRY_TIMES` |
| 私有成员 | `_leading_underscore` | `_build_query` |

**类型注解示例：**
```python
def create_user(username: str, password: str) -> User:
    ...
```

### 6.2 注释规范

- 注释以“解释为什么”优先，不重复“代码做了什么”。

```python
def get_user(user_id: int) -> User:
    # 直接查询数据库可能导致性能问题，使用缓存优化
    cached_user = cache.get(f"user:{user_id}")
    if cached_user:
        return cached_user
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        cache.set(f"user:{user_id}", user, ttl=3600)
    return user
```

## 七、开发环境

## 7.1 docker compose

使用 docker 部署 PostgresSQL 和 redis, 前后端则使用本地环境开发，方便 debug。


## 7.2 uv

uv 是一个 Python 项目管理工具，类似于 npm 或 pnpm。uv 集成了依赖管理、虚拟环境、脚本运行等功能。

```
uv sync # 安装依赖
uv run python main.py # 运行项目
uvx black . # 格式化代码
uvx ruff check . # 静态检查
```

## 7.3 pnpm

pnpm 是一个 node.js 包管理器，相比 npm, pnpm 速度更快，且对国内网络更友好。

## 7.4 husky

Husky 是一个 Git hooks 工具，可以在提交代码前自动执行脚本，确保代码质量。

在根目录下执行以下命令安装并准备husky
```bash
pnpm install
pnpm run prepare
```