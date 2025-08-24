from extensions import db
from datetime import datetime, timezone


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.BigInteger, primary_key=True)


class Visitor(BaseModel):
    """用户信息表"""
    __tablename__ = 'visitor'
    
    # 飞书用户ID相关字段
    open_id = db.Column(db.String(64), unique=True, nullable=False, comment='用户在应用中的唯一标识')
    user_id = db.Column(db.String(64), unique=True, nullable=True, comment='用户在租户内的唯一标识')
    union_id = db.Column(db.String(64), unique=True, nullable=True, comment='用户在应用开发商下的唯一标识')
    
    # 用户基本信息
    name = db.Column(db.String(100), nullable=True, comment='用户姓名')
    email = db.Column(db.String(100), nullable=True, comment='用户邮箱')
    mobile = db.Column(db.String(20), nullable=True, comment='用户手机号')
    avatar_url = db.Column(db.String(255), nullable=True, comment='用户头像URL')
    department = db.Column(db.String(255), nullable=True, comment='用户部门')
    
    # 状态字段
    is_active = db.Column(db.Boolean, default=True, comment='用户是否激活')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment='更新时间')
    
    def __repr__(self):
        return f'<Visitor {self.name}>'


class Group(BaseModel):
    """群组信息表"""
    __tablename__ = 'group'
    
    # 飞书群组ID
    chat_id = db.Column(db.String(64), unique=True, nullable=False, comment='群组唯一标识')
    
    # 群组基本信息
    name = db.Column(db.String(100), nullable=True, comment='群组名称')
    description = db.Column(db.Text, nullable=True, comment='群组描述')
    avatar_url = db.Column(db.String(255), nullable=True, comment='群组头像URL')
    
    # 群组属性
    owner_open_id = db.Column(db.String(64), nullable=True, comment='群主的open_id')
    owner_user_id = db.Column(db.String(64), nullable=True, comment='群主的user_id')
    
    # 群组类型和状态
    type = db.Column(db.String(20), default='group', comment='群组类型: group(普通群), topic(话题群)')
    is_external = db.Column(db.Boolean, default=False, comment='是否是外部群')
    is_active = db.Column(db.Boolean, default=True, comment='群组是否激活')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment='更新时间')
    
    def __repr__(self):
        return f'<Group {self.name}>'


class Message(BaseModel):
    """消息表"""
    __tablename__ = 'message'
    
    # 飞书消息ID
    message_id = db.Column(db.String(64), unique=True, nullable=False, comment='消息唯一标识')
    
    # 消息来源和目标
    sender_open_id = db.Column(db.String(64), nullable=True, comment='发送者open_id')
    sender_user_id = db.Column(db.String(64), nullable=True, comment='发送者user_id')
    receiver_type = db.Column(db.String(20), nullable=False, comment='接收者类型: user, group')
    receiver_id = db.Column(db.String(64), nullable=False, comment='接收者ID(用户ID或群组ID)')
    
    # 消息内容
    message_type = db.Column(db.String(20), nullable=False, comment='消息类型: text, image, file, post, card')
    content = db.Column(db.Text, nullable=False, comment='消息内容')
    
    # 消息状态
    is_read = db.Column(db.Boolean, default=False, comment='消息是否已读')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment='更新时间')
    
    def __repr__(self):
        return f'<Message {self.message_id}>'


class GroupMember(BaseModel):
    """用户与群组关联表"""
    __tablename__ = 'group_member'
    
    visitor_id = db.Column(db.BigInteger, db.ForeignKey('visitor.id'), nullable=False, comment='用户ID')
    group_id = db.Column(db.BigInteger, db.ForeignKey('group.id'), nullable=False, comment='群组ID')
    
    # 用户在群组中的角色
    role = db.Column(db.String(20), default='member', comment='用户角色: owner(群主), admin(管理员), member(成员)')
    is_active = db.Column(db.Boolean, default=True, comment='关联是否激活')
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), comment='加入时间')
    
    # 关联关系
    visitor = db.relationship('Visitor', backref=db.backref('group_memberships', lazy='dynamic'))
    group = db.relationship('Group', backref=db.backref('members', lazy='dynamic'))
    
    def __repr__(self):
        return f'<GroupMember visitor_id={self.visitor_id} group_id={self.group_id}>'

