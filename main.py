import os
import hashlib
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify
import redis
from lark_oapi import Client
from dotenv import load_dotenv
import asyncio
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

# 加载环境变量
load_dotenv()

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_filename = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('feishu-bot')

# 初始化Flask应用
app = Flask(__name__)

# 初始化数据库扩展
from extensions import db, migrate

# 初始化Redis连接
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=True
)

# 初始化飞书客户端
feishu_client = Client()
# 设置应用ID和密钥
feishu_client.app_id = os.getenv('FEISHU_APP_ID')
feishu_client.app_secret = os.getenv('FEISHU_APP_SECRET')

# 消息去重检查
def is_duplicate_message(message_id: str, content: str) -> bool:
    key = f'feishu:message:{message_id}'
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    # 检查消息是否已存在
    existing_hash = redis_client.get(key)
    if existing_hash == content_hash:
        return True
    
    # 存储新消息哈希，设置过期时间（5分钟）
    redis_client.setex(key, 300, content_hash)
    return False

# 消息入队
def enqueue_message(message: dict):
    logger.info(f'Message enqueued: {message}')
    redis_client.lpush('feishu:queue:matrix', json.dumps(message))

def deep_get(d, keys, default=None):
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d

# 消息处理函数
def process_message(message: dict):
    header = message.get('header', {})
    event = message.get('event', {})
    msg = event.get('message', {})
    sender = event.get('sender', {})
    sender_id_obj = sender.get('sender_id', {})

    event_type = header.get('event_type')
    logger.info(f'Processing message: {event_type} - {header.get("event_id")})')

    if event_type == 'im.message.receive_v1':
        if msg.get('message_type') == 'text':
            content = msg.get('content')
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except Exception as e:
                    logger.error(f'Error parsing content: {content}, error: {str(e)}')
                    return
            text = content.get('text')
            if text:
                # 只传递字符串类型的 receive_id
                receive_id = sender_id_obj.get("user_id") or sender_id_obj.get("open_id")
                receive_id_type = "user_id" if sender_id_obj.get("user_id") else "open_id"
                if not receive_id:
                    logger.error("No valid user_id or open_id found in sender_id")
                    return
                send_feishu_message(
                    receive_id_type,
                    receive_id,
                    "text",
                    {"text": "你好哇，我叫百晓生"}
                )

# 消息消费循环
def message_consumer():
    import threading
    def consume():
        while True:
            try:
                result = redis_client.brpop('feishu:queue:matrix', timeout=30)
                if result is not None:
                    _, message_str = result
                    message = json.loads(message_str)  # 用json.loads解析
                    process_message(message)
            except Exception as e:
                logger.error(f'Error consuming message: {str(e)}')
    # 在后台线程启动消费者
    threading.Thread(target=consume, daemon=True).start()

# 飞书事件回调接口
@app.route('/feishu/event', methods=['POST'])
def feishu_event():
    try:
        data = request.json
        logger.info(f'Received feishu event: {json.dumps(data)}')
        
        # 处理challenge验证
        if 'challenge' in data:
            return jsonify({'challenge': data['challenge']})
        
        # 消息去重检查
        event_id = data.get('header', {}).get('event_id')
        if is_duplicate_message(event_id, str(data)):
            logger.warning(f'Duplicate message: {event_id}')
            return jsonify({'status': 'success'})
        
        # 消息入队
        enqueue_message(data)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f'Error processing event: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

def send_feishu_message(receive_id_type: str, receive_id: str, msg_type: str, content: dict):
    from lark_oapi.api.im.v1 import CreateMessageRequest

    req = CreateMessageRequest(
        receive_id_type=receive_id_type,
        body={
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": json.dumps(content, ensure_ascii=False)
        }
    )
    try:
        resp = feishu_client.im.v1.message.create(req)
        if resp.code == 0:
            logger.info(f'Message sent successfully: {resp.data.message_id}')
            return True, resp.data.message_id
        else:
            logger.error(f'Failed to send message: {resp.msg}')
            return False, resp.msg
    except Exception as e:
        logger.error(f'Error sending message: {str(e)}')
        return False, str(e)

def create_app():
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'sqlite:///app.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {'pool_pre_ping': True})

    db.init_app(app)

    # 确保模型被导入，使迁移能够发现
    try:
        import models  # noqa: F401
    except Exception as e:
        logger.warning(f'Failed to import models: {e}')

    # SQLite 迁移友好：启用批量渲染以兼容 ALTER TABLE 等操作
    migrate.init_app(app, db, render_as_batch=True)

    return app

def main():
    # 初始化应用（数据库与迁移）
    create_app()

    # 启动消息消费者
    message_consumer()

    # 启动Flask应用
    port = int(os.getenv('FLASK_PORT', 8000))
    logger.info(f'Starting Flask server on port {port}')
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()
