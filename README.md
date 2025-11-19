# FeedGrep

一个简单的RSS订阅处理器，可以从配置文件中读取RSS地址，定时请求并保存新内容。

## 功能特点

- 从配置文件读取RSS地址
- 支持RSS地址分类
- 支持为每个RSS源设置名称
- 定时请求RSS源
- 自动去重，仅保存新内容
- 将数据存储在SQLite数据库中

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
interval_minutes: 30
```

## 使用方法

运行以下命令启动FeedGrep处理器：

```bash
python feedgrep.py
```

程序会立即检查所有RSS源，然后按照设定的时间间隔定期检查。

## 数据存储

RSS条目被存储在本地的SQLite数据库 `feedgrep.db` 中，每条记录都会标记其所属的分类和来源名称。