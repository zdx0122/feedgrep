import yaml
import sqlite3
import hashlib
import schedule
import time
import feedparser
from datetime import datetime
from typing import List, Dict


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
            print(f"Error fetching RSS feed from {url}: {e}")
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
            
            print(f"[{category} - {source_name}] Saved new item: {item['title']}")
            return True
        except sqlite3.IntegrityError:
            # 可能是唯一约束冲突（并发情况下）
            return False
        except Exception as e:
            print(f"Error saving item: {e}")
            return False
    
    def process_feed(self, url: str, category: str, source_name: str):
        """
        处理单个RSS源
        
        Args:
            url: RSS源地址
            category: RSS源所属类别
            source_name: RSS源名称
        """
        print(f"Processing feed: {source_name} ({url}) - Category: {category}")
        items = self.fetch_rss_feed(url)
        
        new_items_count = 0
        for item in items:
            if self.save_item(item, category, source_name):
                new_items_count += 1
        
        print(f"Feed {source_name} processed. {new_items_count} new items saved.")
    
    def process_all_feeds(self):
        """处理所有配置的RSS源"""
        print("Starting to process all feeds...")
        
        # 处理分类的RSS源
        categories = self.config.get('categories', {})
        for category, feeds in categories.items():
            for feed in feeds:
                source_name = feed.get('name', 'Unknown')
                url = feed.get('url', '')
                if url:
                    self.process_feed(url, category, source_name)
        
        print("All feeds processed.")
    
    def start_scheduler(self):
        """启动定时调度器"""
        interval = self.config.get('interval_minutes', 30)
        
        # 安排定时任务
        schedule.every(interval).minutes.do(self.process_all_feeds)
        
        # 立即执行一次
        self.process_all_feeds()
        
        print(f"Scheduler started. Checking RSS feeds every {interval} minutes.")
        print("Press Ctrl+C to stop.")
        
        # 持续运行调度器
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次是否有需要运行的任务
        except KeyboardInterrupt:
            print("\nScheduler stopped.")


def main():
    """主函数"""
    # 创建FeedGrep处理器实例
    processor = FeedGrepProcessor('feedgrep.yaml')
    
    # 启动定时调度器
    processor.start_scheduler()


if __name__ == "__main__":
    main()