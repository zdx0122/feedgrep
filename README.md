# FeedGrep

一个简单的RSS订阅处理器，可以从配置文件中读取RSS地址，定时请求并保存新内容。

## 功能特点

- 从配置文件读取RSS地址
- 支持RSS地址分类
- 支持为每个RSS源设置名称
- 定时请求RSS源
- 自动去重，仅保存新内容
- 将数据存储在SQLite数据库中
- 提供Web界面浏览和搜索RSS内容
- 高级关键词筛选功能（普通词、必须词、排除词）
- 自定义关键词快捷搜索

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

修改 `feedgrep.yaml` 文件来设置RSS源和检查间隔：

```yaml
categories:
  news:  # 新闻资讯分类
    - name: 少数派
      url: https://sspai.com/feed
    - name: 36氪
      url: https://www.36kr.com/feed
  tech:  # 科技数码分类
    - name: 阮一峰
      url: https://www.ruanyifeng.com/blog/atom.xml
    - name: V2EX-最新
      url: https://rsshub.rssforever.com/v2ex/topics/latest
  
# 默认关键字配置
default_keywords:
  - AI 人工智能 模型 -air -gai -mail
  - 纳斯达克 标普 道琼斯
  - 比特币 以太坊
interval_minutes: 30
```

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