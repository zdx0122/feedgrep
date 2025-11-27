import yaml
import sqlite3
import schedule
import time
import feedparser
import argparse
import sys
import threading
from typing import List, Dict
from utils.Logger import get_logger

# 初始化全局日志记录器
log = get_logger(__name__)


class FeedGrepProcessor:
    def __init__(self, config_path: str, db_path: str = "feedgrep.db"):
        """
        初始化FeedGrep处理器
        
        Args:
            config_path: 配置文件路径
            db_path: SQLite数据库路径
        """
        # 加载配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 初始化数据库
        self.db_path = db_path
        self.init_database()
        
        # 初始化推送管理器
        from push import PushManager
        self.push_manager = PushManager(self.config)
        
        # 存储每个源的新条目用于推送
        self.feed_new_items = {}
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建表来存储RSS条目
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedgrep_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT UNIQUE,
                description TEXT,
                pub_date TEXT,
                guid TEXT UNIQUE,
                category TEXT,
                source_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引来提高查询速度
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guid ON feedgrep_items(guid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_link ON feedgrep_items(link)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON feedgrep_items(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_name ON feedgrep_items(source_name)')
        
        conn.commit()
        conn.close()
    
    def fetch_rss_feed(self, url: str) -> List[Dict]:
        """
        获取并解析RSS源
        
        Args:
            url: RSS源地址
            
        Returns:
            解析后的RSS条目列表
        """
        try:
            # 设置feedparser的超时和代理（如果需要）
            import socket
            socket.setdefaulttimeout(30)
            feed = feedparser.parse(url)
            items = []
            
            for entry in feed.entries:
                # 提取关键字段
                item = {
                    'title': getattr(entry, 'title', ''),
                    'link': getattr(entry, 'link', ''),
                    'description': getattr(entry, 'summary', ''),
                    'pub_date': getattr(entry, 'published', ''),
                    'guid': getattr(entry, 'id', getattr(entry, 'link', ''))
                }
                
                items.append(item)
            
            return items
        except Exception as e:
            log.error(f"Error fetching RSS feed from {url}: {e}")
            return []
    
    def is_item_exists(self, guid: str, link: str) -> bool:
        """
        检查条目是否已存在
        
        Args:
            guid: 条目的GUID
            link: 条目的链接
            
        Returns:
            如果条目已存在返回True，否则返回False
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT COUNT(*) FROM feedgrep_items WHERE guid = ? OR link = ?', 
            (guid, link)
        )
        count = cursor.fetchone()[0]
        
        conn.close()
        return count > 0
    
    def save_item(self, item: Dict, category: str, source_name: str) -> bool:
        """
        保存单个RSS条目到数据库
        
        Args:
            item: RSS条目字典
            category: 条目所属类别
            source_name: RSS源名称
            
        Returns:
            保存成功返回True，否则返回False
        """
        # 检查条目是否已存在
        if self.is_item_exists(item['guid'], item['link']):
            return False  # 条目已存在，不需要保存
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO feedgrep_items (title, link, description, pub_date, guid, category, source_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['title'],
                item['link'],
                item['description'],
                item['pub_date'],
                item['guid'],
                category,
                source_name
            ))
            
            conn.commit()
            conn.close()
            
            log.info(f"[{category} - {source_name}] Saved new item: {item['title']}")
            
            # 记录新条目用于推送
            if source_name not in self.feed_new_items:
                self.feed_new_items[source_name] = []
            self.feed_new_items[source_name].append(item)
            
            return True
        except sqlite3.IntegrityError:
            # 可能是唯一约束冲突（并发情况下）
            return False
        except Exception as e:
            log.error(f"Error saving item: {e}")
            return False
    
    def process_feed(self, url: str, category: str, source_name: str):
        """
        处理单个RSS源
        
        Args:
            url: RSS源地址
            category: RSS源所属类别
            source_name: RSS源名称
        """
        log.info(f"Processing feed: {source_name} ({url}) - Category: {category}")
        items = self.fetch_rss_feed(url)
        
        new_items_count = 0
        for item in items:
            if self.save_item(item, category, source_name):
                new_items_count += 1
        
        log.info(f"Feed {source_name} processed. {new_items_count} new items saved.")
        
        # 推送RSS源的新内容
        feed_config_list = self.config.get('categories', {}).get(category, [])
        feed_config = None
        for fc in feed_config_list:
            if fc.get('name') == source_name:
                feed_config = fc
                break
                
        if feed_config and new_items_count > 0:
            push_channels = feed_config.get('push_channels', [])
            if push_channels:
                title = f"[FeedGrep] {source_name} 有 {new_items_count} 条新内容\n"
                content = ""
                
                for i, item in enumerate(self.feed_new_items.get(source_name, []), 1):
                    # 添加序号和超链接到内容
                    content += f"\n{i}. [{item['title']}]({item['link']})\n"
                    
                    # 限制总内容长度
                    if len(content) > 1500:
                        content += f"\n... 还有更多内容（共{new_items_count}条）"
                        break
                        
                self.push_manager.send_bulk_push(push_channels, title, content)
    
    def process_all_feeds(self):
        """处理所有配置的RSS源"""
        log.info("Starting to process all feeds...")
        
        # 清空之前的新条目记录
        self.feed_new_items = {}
        
        # 处理分类的RSS源
        categories = self.config.get('categories', {})
        for category, feeds in categories.items():
            for feed in feeds:
                source_name = feed.get('name', 'Unknown')
                url = feed.get('url', '')
                if url:
                    try:
                        self.process_feed(url, category, source_name)
                    except Exception as e:
                        log.error(f"Failed to process feed {source_name} ({url}): {e}")
        
        # 处理关键词推送
        self.process_keyword_pushes()
        
        log.info("All feeds processed.")

    def process_keyword_pushes(self):
        """处理基于关键词的推送"""
        if not self.push_manager.push_enabled:
            return
            
        # 获取默认关键词配置
        default_keywords = self.config.get('default_keywords', [])
        
        # 遍历每个关键词配置
        for i, keyword_config in enumerate(default_keywords):
            # 检查是否有针对此关键词的推送配置
            keyword_push_config = None
            if isinstance(keyword_config, dict):
                keyword_push_config = keyword_config
                keyword_expr = keyword_config.get('keywords', '')
            else:
                keyword_expr = keyword_config
                
            # 如果没有推送配置，跳过
            if isinstance(keyword_push_config, dict) and 'push_channels' not in keyword_push_config:
                continue
                
            push_channels = keyword_push_config.get('push_channels', []) if isinstance(keyword_push_config, dict) else []
            if not push_channels:
                continue
            
            # 搜索匹配该关键词的内容
            matched_items = self.search_items_by_keyword(keyword_expr)
            
            # 如果有匹配的内容，则发送推送
            if matched_items:
                # 构造推送标题和内容
                first_keyword = keyword_expr.split()[0]  # 取第一个关键词作为标题的一部分
                title = f"[FeedGrep关键词] {first_keyword} 有 {len(matched_items)} 条新内容"
                
                content = ""

                for i, item in enumerate(matched_items[:10], 1):  # 限制最多10条
                    # 添加序号、来源和超链接到内容
                    content += f"\n{i}. [{item['source_name']}] [{item['title']}]({item['link']})\n"
                    
                if len(matched_items) > 10:
                    content += f"\n... 还有 {len(matched_items) - 10} 条内容"
                    
                # 发送推送
                self.push_manager.send_bulk_push(push_channels, title, content)

    def search_items_by_keyword(self, keyword):
        """
        根据关键词搜索新条目
        
        Args:
            keyword: 关键词表达式
            
        Returns:
            匹配的条目列表
        """
        try:
            # 解析关键词语法
            required_keywords = []  # 必须包含的关键词 (+)
            excluded_keywords = []  # 必须排除的关键词 (-)
            normal_keywords = []    # 普通关键词 (空格分隔)
            
            # 解析关键词
            parts = keyword.split()
            for part in parts:
                if part.startswith('+'):
                    required_keywords.append(part[1:])  # 去掉+号
                elif part.startswith('-'):
                    excluded_keywords.append(part[1:])  # 去掉-号
                else:
                    normal_keywords.append(part)
            
            # 获取爬取频率作为时间范围
            interval_minutes = self.config.get('interval_minutes', 30)
            
            # 构建查询语句
            query_conditions = [f"created_at >= datetime('now', '-{interval_minutes} minutes')"]  # 只查找最近几次爬取周期内的新内容
            params = []
            
            # 处理普通关键词 (OR关系)
            if normal_keywords:
                or_conditions = []
                for kw in normal_keywords:
                    or_conditions.append("(title LIKE ? OR description LIKE ?)")
                    params.extend([f"%{kw}%", f"%{kw}%"])
                query_conditions.append("(" + " OR ".join(or_conditions) + ")")
            
            # 处理必须关键词 (AND关系)
            for kw in required_keywords:
                query_conditions.append("(title LIKE ? OR description LIKE ?)")
                params.extend([f"%{kw}%", f"%{kw}%"])
            
            # 处理排除关键词
            for kw in excluded_keywords:
                query_conditions.append("(title NOT LIKE ? AND description NOT LIKE ?)")
                params.extend([f"%{kw}%", f"%{kw}%"])
            
            # 基础查询
            query = "SELECT * FROM feedgrep_items WHERE " + " AND ".join(query_conditions)
            query += " ORDER BY created_at DESC"
            
            # 执行查询
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # 获取结果
            rows = cursor.fetchall()
            items = [dict(row) for row in rows]
            
            conn.close()
            
            return items
        except Exception as e:
            log.error(f"搜索关键词 '{keyword}' 时出错: {e}")
            return []
    
    def start_scheduler(self):
        """启动定时调度器"""
        interval = self.config.get('interval_minutes', 30)
        
        # 安排定时任务
        schedule.every(interval).minutes.do(self.process_all_feeds)
        
        # 立即执行一次
        self.process_all_feeds()
        
        log.info(f"Scheduler started. Checking RSS feeds every {interval} minutes.")
        
        # 持续运行调度器
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次是否有需要运行的任务
    
    def start_scheduler_async(self):
        """异步启动定时调度器"""
        scheduler_thread = threading.Thread(target=self.start_scheduler, daemon=True)
        scheduler_thread.start()
        return scheduler_thread


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FeedGrep - RSS聚合器')
    parser.add_argument('--host', default='0.0.0.0', help='API服务监听地址')
    parser.add_argument('--port', type=int, default=8000, help='API服务端口')
    
    args = parser.parse_args()
    
    # 创建FeedGrep处理器实例
    processor = FeedGrepProcessor('feedgrep.yaml')
    
    # 异步启动定时调度器
    scheduler_thread = processor.start_scheduler_async()
    log.info("Scheduler started in background thread")
    
    # 启动API服务
    try:
        from api import FeedGrepAPI
        api = FeedGrepAPI('feedgrep.yaml')
        log.info(f"Starting API server on {args.host}:{args.port}")
        api.run(host=args.host, port=args.port)
    except ImportError as e:
        log.error(f"无法导入API模块: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()