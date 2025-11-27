import yaml
import sqlite3
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Optional
import uvicorn


class FeedGrepAPI:
    def __init__(self, config_path: str, db_path: str = "feedgrep.db"):
        """
        初始化FeedGrep API服务
        
        Args:
            config_path: 配置文件路径
            db_path: SQLite数据库路径
        """
        # 加载配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.db_path = db_path
        self.app = FastAPI(
            title="FeedGrep API",
            description="RSS聚合器API服务",
            version="1.0.0"
        )
        
        # 添加CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
        
        # 挂载静态文件目录，提供index.html和其他静态资源
        # 注意：这必须在设置路由之后，以避免拦截API请求
        self.app.mount("/", StaticFiles(directory=".", html=True), name="static")
    
    def _setup_routes(self):
        """设置API路由"""
        self.app.get("/api/feeds", response_model=dict)(self.get_feeds)
        self.app.get("/api/items", response_model=dict)(self.get_items)
        self.app.get("/api/categories", response_model=dict)(self.get_categories)
        self.app.get("/api/search", response_model=dict)(self.search_items)
        self.app.get("/api/default_keywords", response_model=dict)(self.get_default_keywords)
        self.app.get("/health", response_model=dict)(self.health_check)
    
    async def get_feeds(self):
        """
        获取所有RSS源和分类信息
        
        Returns:
            JSON格式的所有RSS源和分类信息
        """
        try:
            categories_data = self.config.get('categories', {})
            return {
                'success': True,
                'data': categories_data,
                'count': sum(len(feeds) for feeds in categories_data.values())
            }
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': str(e)
                }
            )
    
    async def get_categories(self):
        """
        获取所有分类信息
        
        Returns:
            JSON格式的所有分类信息
        """
        try:
            categories_data = self.config.get('categories', {})
            categories = list(categories_data.keys())
            return {
                'success': True,
                'data': categories,
                'count': len(categories)
            }
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': str(e)
                }
            )
    
    async def get_default_keywords(self):
        """
        获取默认关键字列表
        
        Returns:
            JSON格式的默认关键字列表
        """
        try:
            default_keywords = self.config.get('default_keywords', [])
            # 处理新的关键词格式，提取关键词表达式
            processed_keywords = []
            for keyword_config in default_keywords:
                if isinstance(keyword_config, dict):
                    # 新格式：包含 keywords 和 push_channels 字段的对象
                    processed_keywords.append(keyword_config['keywords'])
                else:
                    # 旧格式：直接是关键词字符串
                    processed_keywords.append(keyword_config)
            
            return {
                'success': True,
                'data': processed_keywords,
                'count': len(processed_keywords)
            }
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': str(e)
                }
            )

    async def get_items(
        self,
        category: Optional[str] = Query(None, description="按分类筛选"),
        source: Optional[str] = Query(None, description="按来源筛选"),
        keyword: Optional[str] = Query(None, description="关键字搜索"),
        limit: int = Query(10, ge=1, le=1000, description="返回数量限制"),
        offset: int = Query(0, ge=0, description="偏移量")
    ):
        """
        从数据库获取RSS条目，支持查询参数
        
        查询参数:
            category: 分类筛选
            source: 来源筛选
            keyword: 关键字搜索
            limit: 返回数量限制，默认50，最大1000
            offset: 偏移量，默认0
            
        Returns:
            JSON格式的RSS条目数据
        """
        try:
            # 构建查询语句
            query = "SELECT * FROM feedgrep_items WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if source:
                query += " AND source_name = ?"
                params.append(source)
                
            if keyword:
                # 解析关键词语法
                # 普通词：包含其中任意一个词就会被捕获，多个关键词使用空格分隔
                # 必须词：必须同时包含普通词和必须词才会被捕获，使用+分隔  
                # 排除词：包含过滤词的新闻会被直接排除，即使包含关键词，使用-分隔
                
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
                
                # 处理普通关键词 (OR关系)
                if normal_keywords:
                    or_conditions = []
                    for kw in normal_keywords:
                        or_conditions.append("(title LIKE ? OR description LIKE ?)")
                        params.extend([f"%{kw}%", f"%{kw}%"])
                    query += " AND (" + " OR ".join(or_conditions) + ")"
                
                # 处理必须关键词 (AND关系)
                for kw in required_keywords:
                    query += " AND (title LIKE ? OR description LIKE ?)"
                    params.extend([f"%{kw}%", f"%{kw}%"])
                
                # 处理排除关键词
                for kw in excluded_keywords:
                    query += " AND (title NOT LIKE ? AND description NOT LIKE ?)"
                    params.extend([f"%{kw}%", f"%{kw}%"])
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # 执行查询
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # 获取结果
            rows = cursor.fetchall()
            items = [dict(row) for row in rows]
            
            conn.close()
            
            return {
                'success': True,
                'data': items,
                'count': len(items)
            }
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': str(e)
                }
            )
    
    async def search_items(
        self,
        keyword: str = Query(..., description="搜索关键字"),
        category: Optional[str] = Query(None, description="按分类筛选"),
        source: Optional[str] = Query(None, description="按来源筛选"),
        limit: int = Query(50, ge=1, le=1000, description="返回数量限制"),
        offset: int = Query(0, ge=0, description="偏移量")
    ):
        """
        搜索RSS条目
        
        查询参数:
            keyword: 搜索关键字（必填）
            category: 分类筛选
            source: 来源筛选
            limit: 返回数量限制，默认50，最大1000
            offset: 偏移量，默认0
            
        Returns:
            JSON格式的RSS条目数据
        """
        try:
            # 解析关键词语法
            # 普通词：包含其中任意一个词就会被捕获，多个关键词使用空格分隔
            # 必须词：必须同时包含普通词和必须词才会被捕获，使用+分隔  
            # 排除词：包含过滤词的新闻会被直接排除，即使包含关键词，使用-分隔
            
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
            
            # 构建查询语句
            query_conditions = []
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
            query = "SELECT * FROM feedgrep_items WHERE "
            if query_conditions:
                query += " AND ".join(query_conditions)
            else:
                query += "1=1"  # 没有条件时的占位符
            
            # 添加分类和来源筛选条件
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if source:
                query += " AND source_name = ?"
                params.append(source)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # 执行查询
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # 获取结果
            rows = cursor.fetchall()
            items = [dict(row) for row in rows]
            
            conn.close()
            
            return {
                'success': True,
                'data': items,
                'count': len(items),
                'keyword': keyword
            }
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': str(e)
                }
            )
    
    async def health_check(self):
        """
        健康检查接口
        
        Returns:
            健康状态信息
        """
        return {
            'status': 'healthy',
            'service': 'FeedGrep API'
        }
    
    def run(self, host='127.0.0.1', port=8000, **kwargs):
        """
        通过uvicorn启动API服务
        
        Args:
            host: 监听主机地址
            port: 监听端口
            **kwargs: 传递给uvicorn的其他参数
        """
        uvicorn.run(self.app, host=host, port=port, **kwargs)