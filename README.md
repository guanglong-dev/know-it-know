# 飞书机器人项目

一个基于Python Flask和Redis的飞书机器人应用，实现消息接收、处理、发送的完整流程。

## 功能特点
- 使用Flask创建HTTP接口接收飞书事件
- 基于Redis实现消息去重和消息队列
- 完整的日志系统，记录请求和响应详情
- 支持多种消息类型发送（文本、卡片、富文本等）
- 异步消息处理，避免阻塞主进程

## 技术栈
- **开发语言**: Python 3.13.5
- **Web框架**: Flask 3.1.1
- **依赖管理**: uv
- **飞书SDK**: lark-oapi 1.4.19
- **消息队列**: Redis
- **配置管理**: python-dotenv

## 项目结构
```
know-it-all/
├── .env                # 环境变量配置
├── .gitignore          # Git忽略文件
├── main.py             # 应用入口文件
├── pyproject.toml      # 项目依赖配置
├── README.md           # 项目文档
├── logs/               # 日志文件目录
└── uv.lock             # uv依赖锁定文件
```

## 安装步骤

### 前提条件
- Python 3.13.5+ 已安装
- Redis 服务器已安装并运行
- uv 包管理器已安装 (`pip install uv`)

### 安装依赖
```bash
# 克隆仓库
git clone <repository-url>
cd know-it-all

# 安装依赖
uv sync
```

## 配置说明

1. 复制环境变量模板并修改配置：
```bash
cp .env.example .env
```

2. 编辑.env文件，填入必要配置：
```ini
# 飞书应用配置
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_ENCRYPT_KEY=your_encrypt_key  # 可选

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 应用配置
FLASK_PORT=8000

# 数据库（可选，MySQL 示例；未配置则使用 sqlite:///app.db）
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4
```

## 运行应用
```bash
# 启动应用
uv run main.py
```

应用将在 http://localhost:8000 启动，飞书事件接收端点为 `/feishu/event`

## 飞书配置
1. 在飞书开放平台创建应用
2. 配置事件订阅回调地址为 `http://your-domain:8000/feishu/event`
3. 启用所需的事件类型
4. 配置应用权限

## 消息处理流程
1. **接收消息**: Flask接口接收飞书事件，进行验证和去重检查
2. **消息入队**: 合法消息存入Redis消息队列
3. **异步处理**: 后台线程消费队列消息并处理
4. **发送响应**: 根据业务逻辑调用飞书API发送消息

## 日志说明
- 日志文件存储在 `logs/` 目录，按日期命名
- 日志包含请求详情、处理结果和错误信息
- 同时输出到控制台和文件

## 扩展开发
消息处理逻辑在 `process_message` 函数中实现，可根据不同 `event_type` 添加业务逻辑：
```python
def process_message(message: dict):
    event_type = message.get('header', {}).get('event_type')
    logger.info(f'Processing message: {event_type} - {message.get('event_id')}')
    # 添加自定义业务逻辑
```

## 许可证
[MIT](LICENSE)

## 数据库迁移

1. 配置数据库连接（MySQL 示例）到 `.env`：
   ```ini
   DATABASE_URL=mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4
   ```
   未配置时默认使用 `sqlite:///app.db`。

2. 初始化迁移目录：
   ```bash
   flask --app main:create_app db init
   ```

3. 生成迁移文件（会自动对比模型变更）：
   ```bash
   flask --app main:create_app db migrate -m "init"
   ```

4. 应用迁移到数据库：
   ```bash
   flask --app main:create_app db upgrade
   ```

5. 回滚一步（如需）：
   ```bash
   flask --app main:create_app db downgrade -1
   ```

在 `models.py` 中定义/修改你的模型后，重复步骤 3-4 以同步表结构。