# FeedGrep - 让重要信息主动找到你 💫

FeedGrep 是一款专注于 RSS 信息捕获、精准筛选和多渠道推送 的轻量级阅读器。
FeedGrep 支持多源 RSS 抓取、自定义筛选规则、多渠道推送和轻量级 Web UI，让你以最低成本构建自己的信息获取系统。

## 功能特点

### 📡 多源订阅
- RSS 源订阅 - 支持主流 RSS 格式
- 灵活定时策略 - 自定义抓取间隔频率

### 🔍 自定义监控筛选
FeedGrep 提供三种关键词规则类型，可组合使用以实现精确过滤：

| 类型   | 描述                     | 示例                   |
|--------|------------------------|----------------------|
| 普通词 | 任意词命中即匹配               | 苹果 手机 |
| 必须词 | 必须全部出现，使用 +前缀（注意中间无空格） | +苹果 +发布会             |
| 排除词 | 出现即过滤，使用 -前缀（注意中间无空格）           | 苹果 -果汁               |

综合示例：

`苹果 华为 +手机 -水果 -价格
`

意为：
命中“苹果”或“华为”，并必须包含“手机”，排除包含“水果”和“价格”的内容。

### 🚀典型应用场景
| 用户角色 | 监控示例            |
|------|-----------------|
| 开发者  | 开源库更新、技术博客、漏洞通告 |
| 购物达人 | 商品降价、限时优惠、新品上市  |
| 市场人员 | 品牌舆情、竞品动态、行业趋势  |
| 普通用户 | 热点新闻、新闻动态、新闻快讯      |
| 投资人员 | 财经新闻、股票行情、行业动态  |

### 🤖 多渠道推送
- 飞书 - 群机器人推送
- 企业微信 - 群机器人
- 微信 - 利用企微-微信插件通道
- Telegram - Bot 消息推送
- 邮件 - SMTP 邮件通知

### ⚙️ 灵活配置
- rss源管理 - 不限制个数、自由配置
- 关键词匹配规则 - 支持普通词、必须词、排除词
- 推送路由 - 单个rss源或者关键词可配置多个推送渠道
- 消息合并 - 同源同关键词信息合并推送
- 总开关控制 - 全局推送启用/禁用


## Docker Compose
拉取源码，进入目录执行 `docker compose up -d` 即可


## 快速开始
### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

修改 `feedgrep.yaml` 文件来设置RSS源、检查间隔、关键词匹配规则、推送渠道。

### 运行

运行以下命令启动FeedGrep处理器：

```bash
python feedgrep.py
```

程序会立即检查所有RSS源，然后按照设定的时间间隔定期检查。

启动后可以通过浏览器访问 `http://localhost:8000` 查看Web界面。

#### Bash 脚本方式 (推荐)

项目提供了一个统一的 Bash 脚本来管理服务：

```bash
# 启动服务
./feedgrep.sh start

# 停止服务
./feedgrep.sh stop

# 重启服务
./feedgrep.sh restart
```

## 本地数据存储

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
3. 个人微信（基于企业微信应用，在企微后台-微信插件，微信扫码关注，推送到个人微信）
3. 邮件
4. Telegram

## 项目结构

```.
├── feedgrep.py           # 主程序入口
├── feedgrep.yaml         # 配置文件
├── feedgrep.db           # SQLite 本地数据
├── feedgrep.sh           # bash启动脚本
├── index.html            # Web UI
├── api.py                # API模块
├── push.py               # 推送模块
└── utils/                # 日志模块
├── requirements.txt      # 依赖包
```


## 配置详解

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
    webhook_qyweixin:
      type: wework
      wework_msg_type: text  # 可选:text, markdown
      url: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=XXXXXXXXXXXXXXXXXX
    
    # 个人微信
    webhook_weixin:
      type: wework
      wework_msg_type: text  # 只可选:text，需要在企微后台扫码关注“微信插件”，其他配置和上述企微机器人一样
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

- `time_restriction_enabled`: 是否启用时间范围控制，默认为false
- `time_start`: 推送开始时间（24小时制，北京时间），默认为"08:00"
- `time_end`: 推送结束时间（24小时制，北京时间），默认为"22:00"

### 为RSS源配置推送渠道

在每个RSS源配置中添加 `push_channels` 列表来指定该源使用哪些推送渠道：

```
categories:
  news:
    - name: 阮一峰的网络日志
      url: https://www.ruanyifeng.com/blog/atom.xml
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

当有新内容匹配关键词时，将会推送到指定的渠道。关键词推送只会推送最近一次RSS获取到的新内容。
