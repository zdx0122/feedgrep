# FeedGrep - 让重要信息主动找到你 💫

轻量级RSS阅读器，支持筛选、推送。

## 功能特点

### 📡 多源信息获取
- RSS 源订阅 - 支持主流 RSS 格式
- 灵活定时策略 - 自定义抓取频率

### 🔍 智能监控筛选
- 关键词规则系统
- 普通词 - 包含任意一个词即被捕获 
  - 示例：苹果 手机 - 包含"苹果"或"手机"即匹配
- 必须词 - 必须同时包含所有指定词
  - 格式：+必须词1 +必须词2 
  - 示例：+苹果 +发布会 
    - 必须同时包含"苹果"和"发布会"
- 排除词 - 包含即过滤 
  - 格式：-排除词 
  - 示例：苹果 -果汁 
    - 包含"苹果"但不包含"果汁"
### 应用场景
#### 🚀 开发者
- 监控依赖库版本更新
- 跟踪技术博客最新文章
- 获取开源项目发布通知

#### 🛒 购物达人
- 监控商品价格波动
- 获取限时优惠信息
- 关注新品发布动态

#### 📊 市场人员
- 品牌舆情监控
- 竞品动态跟踪
- 行业资讯收集

#### 🏢 企业应用
- 内部系统监控
- 业务指标预警
- 竞争对手情报收集

### 🤖 多渠道推送
- 企业微信 - 个人消息及群机器人
- 飞书 - 群机器人推送
- 邮件 - SMTP 邮件通知
- Telegram - Bot 消息推送

### ⚙️ 灵活配置
- 多任务管理 - 同时运行多个监控任务
- 推送路由 - 单个源可配置多个推送渠道
- 消息合并 - 同源同关键词信息合并推送
- 总开关控制 - 全局推送启用/禁用



## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

修改 `feedgrep.yaml` 文件来设置RSS源、检查间隔、关键词匹配规则、推送渠道。

## 使用方法

运行以下命令启动FeedGrep处理器：

```bash
python feedgrep.py
```

程序会立即检查所有RSS源，然后按照设定的时间间隔定期检查。

启动后可以通过浏览器访问 `http://localhost:8000` 查看Web界面。

## 服务管理

### Bash 脚本方式 (推荐)

项目提供了一个统一的 Bash 脚本来管理服务：

```bash
# 启动服务
./feedgrep.sh start

# 停止服务
./feedgrep.sh stop

# 重启服务
./feedgrep.sh restart
```

## 数据存储

RSS条目被存储在本地的SQLite数据库 `feedgrep.db` 中，每条记录都会标记其所属的分类和来源名称。

## 高级关键词搜索语法

FeedGrep支持三种关键词类型，可以通过组合使用实现精确的内容筛选：

1. **普通词**：包含其中任意一个词就会被捕获，多个关键词使用空格分隔
   - 示例：`苹果 华为` 表示包含"苹果"或"华为"的内容

2. **必须词**：必须同时包含普通词和必须词才会被捕获，使用`+`前缀标识
   - 示例：`苹果 +手机` 表示包含"苹果"且必须包含"手机"的内容

3. **排除词**：包含过滤词的新闻会被直接排除，即使包含其他关键词，使用`-`前缀标识
   - 示例：`苹果 -水果` 表示包含"苹果"但排除包含"水果"的内容

完整示例：`苹果 华为 +手机 -水果 -价格` 表示搜索包含"苹果"或"华为"，同时必须包含"手机"，但排除包含"水果"或"价格"的内容。

## 自定义关键词快捷搜索

在Web界面左侧边栏中提供了默认关键词的快捷按钮，点击即可快速进行相关搜索。为了保持界面美观，按钮上仅显示关键词组的第一个词，鼠标悬停时会显示完整的关键词配置。

## 推送功能

FeedGrep支持将新的RSS条目推送到多种渠道：

### 支持的推送渠道

1. 飞书群机器人
2. 企业微信群机器人
3. 邮件
4. Telegram

### 配置推送渠道

在配置文件中添加 `push` 部分来启用推送功能：

```
push:
  # 推送总开关
  enabled: true
  
  # 推送时间范围控制开关
  time_restriction_enabled: true
  
  # 推送时间范围（24小时制，北京时间）
  time_start: "08:00"  # 早上8点
  time_end: "22:00"    # 晚上10点
  
  # 推送渠道配置
  webhooks:
    # 飞书资讯群
    webhook_feishu:
      type: feishu
      url: https://open.feishu.cn/open-apis/bot/v2/hook/XXXXXXXXXXXXXXXXXX
    
    # 企业微信群机器人
    webhook_weixin:
      type: wework
      wework_msg_type: text  # 可选:text, markdown
      url: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=XXXXXXXXXXXXXXXXXX
      
    # 邮件推送
    email_notices:
      type: email
      smtp_server: smtp.example.com
      smtp_port: 587
      username: your_username
      password: your_password
      sender: sender@example.com
      receivers:
        - receiver1@example.com
        - receiver2@example.com
        
    # Telegram推送
    telegram_channel:
      type: telegram
      bot_token: YOUR_BOT_TOKEN
      chat_id: YOUR_CHAT_ID
```

推送时间范围控制功能允许您设置推送消息的有效时间窗口。**时间范围始终按照北京时间进行计算**，无论服务部署在哪个时区。默认情况下，只在早上8点到晚上10点之间推送消息。您可以通过以下配置项控制此功能：

- `time_restriction_enabled`: 是否启用时间范围控制，默认为true
- `time_start`: 推送开始时间（24小时制，北京时间），默认为"08:00"
- `time_end`: 推送结束时间（24小时制，北京时间），默认为"22:00"

例如，如果服务部署在美国洛杉矶，当洛杉矶时间为晚上8点（实际上是北京时间下午1点，因为时差关系）时，由于不在推送时间范围内（8:00-22:00），系统将不会发送推送消息。

### 推送消息格式优化

为了提升大量消息的阅读体验，推送消息体进行了以下优化：

1. **结构化展示**：使用编号列表展示每条消息，清晰明了
2. **超链接支持**：保留完整的超链接，方便直接访问原始内容
3. **长度控制**：对过长的内容进行截断，并提示剩余条目数量
4. **渠道适配**：根据不同推送渠道的特点优化格式展示

推送消息示例：
```
## 竹新社-TG 新增内容 (3条)

1. [标题1](http://example.com/link1)
2. [标题2](http://example.com/link2)
3. [标题3](http://example.com/link3)
```

### 为RSS源配置推送渠道

在每个RSS源配置中添加 `push_channels` 列表来指定该源使用哪些推送渠道：

```
categories:
  news:
    - name: 竹新社-TG
      url: https://rsshub.rssforever.com/telegram/channel/tnews365
      push_channels:
        - webhook_feishu
        - webhook_weixin
```

当该RSS源有新内容时，将会推送到指定的渠道。

### 为关键词配置推送渠道

在关键词配置中添加 `push_channels` 列表来指定匹配该关键词的内容推送到哪些渠道：

```
default_keywords:
  - keywords: AI 人工智能 +模型 -air -gai -mail
    push_channels:
      - webhook_feishu
  - 纳斯达克 标普 道琼斯
```

当有新内容匹配关键词时，将会推送到指定的渠道。关键词推送只会推送最近一小时内获取到的新内容。
