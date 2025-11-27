import requests
import smtplib
import re
from email.mime.text import MIMEText
from email.header import Header
from utils.Logger import get_logger
from datetime import datetime, time
import pytz


log = get_logger(__name__)


class PushManager:
    def __init__(self, config):
        self.config = config
        self.push_enabled = config.get('push', {}).get('enabled', False)
        self.webhooks = config.get('push', {}).get('webhooks', {})
        # 推送时间范围配置
        self.time_restriction_enabled = config.get('push', {}).get('time_restriction_enabled', True)
        self.time_start_str = config.get('push', {}).get('time_start', '08:00')
        self.time_end_str = config.get('push', {}).get('time_end', '22:00')

    def is_within_time_range(self):
        """
        检查当前时间是否在推送时间范围内（北京时间）
        
        Returns:
            bool: 如果在时间范围内返回True，否则返回False
        """
        if not self.time_restriction_enabled:
            return True
            
        try:
            # 获取北京时间
            beijing_tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(beijing_tz)
            current_time = now.time()
            
            # 解析时间范围
            start_time = datetime.strptime(self.time_start_str, '%H:%M').time()
            end_time = datetime.strptime(self.time_end_str, '%H:%M').time()
            
            # 检查是否在时间范围内
            # 考虑跨日期的情况（例如 22:00 到 08:00）
            if start_time <= end_time:
                # 不跨日期，例如 08:00 到 22:00
                return start_time <= current_time <= end_time
            else:
                # 跨日期，例如 22:00 到 08:00
                return current_time >= start_time or current_time <= end_time
        except Exception as e:
            log.error(f"检查推送时间范围时出错: {e}")
            # 出错时默认允许推送
            return True

    def send_push(self, channel_name, title, content):
        """
        发送推送消息到指定渠道
        
        Args:
            channel_name: 渠道名称
            title: 消息标题
            content: 消息内容
        """
        if not self.push_enabled:
            return False

        # 检查是否在推送时间范围内
        if not self.is_within_time_range():
            log.info(f"当前时间不在推送时间范围内 ({self.time_start_str}-{self.time_end_str})，跳过推送")
            return False

        if channel_name not in self.webhooks:
            log.warning(f"推送渠道 {channel_name} 未配置")
            return False

        webhook_config = self.webhooks[channel_name]
        push_type = webhook_config.get('type')

        try:
            if push_type == 'feishu':
                return self._send_feishu(webhook_config, title, content)
            elif push_type == 'wework':
                return self._send_wework(webhook_config, title, content)
            elif push_type == 'email':
                return self._send_email(webhook_config, title, content)
            elif push_type == 'telegram':
                return self._send_telegram(webhook_config, title, content)
            else:
                log.warning(f"不支持的推送类型: {push_type}")
                return False
        except Exception as e:
            log.error(f"推送消息到 {channel_name} 失败: {e}")
            return False

    def _send_feishu(self, config, title, content):
        """发送飞书推送"""
        url = config['url']
        
        # 处理Markdown内容以适配飞书
        processed_content = self._format_feishu_content(content)
        
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [
                            [{
                                "tag": "text",
                                "text": processed_content
                            }]
                        ]
                    }
                }
            }
        }
        response = requests.post(url, json=payload)
        return response.status_code == 200

    def _format_feishu_content(self, content):
        """
        格式化飞书推送内容
        """
        # 简单处理，实际项目中可以实现更复杂的转换逻辑
        return content

    def _send_wework(self, config, title, content):
        """发送企业微信推送"""
        url = config['url']
        msg_type = config.get('wework_msg_type', 'text')
        
        if msg_type == 'text':
            # 企业微信文本消息不支持Markdown，需要转换
            plain_content = self._strip_markdown_format(content)
            payload = {
                "msgtype": "text",
                "text": {
                    "content": f"{title}\n\n{plain_content}"
                }
            }
        elif msg_type == 'markdown':
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"# {title}\n\n{content}"
                }
            }
        else:
            # 默认使用文本消息
            plain_content = self._strip_markdown_format(content)
            payload = {
                "msgtype": "text",
                "text": {
                    "content": f"{title}\n\n{plain_content}"
                }
            }
            
        response = requests.post(url, json=payload)
        return response.status_code == 200

    def _strip_markdown_format(self, content):
        """
        移除Markdown格式，只保留文本内容
        """
        import re
        # 移除Markdown链接格式 [text](url)
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', content)
        # 移除Markdown标题格式
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        # 移除其他Markdown符号
        content = re.sub(r'[*_~`]', '', content)
        return content

    def _send_email(self, config, title, content):
        """发送邮件推送"""
        smtp_server = config['smtp_server']
        smtp_port = config.get('smtp_port', 587)
        username = config['username']
        password = config['password']
        sender = config['sender']
        receivers = config['receivers']

        # 邮件内容处理
        plain_content = self._strip_markdown_format(content)
        # 添加邮件签名
        plain_content += "\n\n---\nFeedGrep RSS推送服务"
        
        message = MIMEText(plain_content, 'plain', 'utf-8')
        message['From'] = Header(sender, 'utf-8')
        message['To'] = Header(','.join(receivers), 'utf-8')
        message['Subject'] = Header(title, 'utf-8')

        try:
            smtp_obj = smtplib.SMTP(smtp_server, smtp_port)
            smtp_obj.starttls()
            smtp_obj.login(username, password)
            smtp_obj.sendmail(sender, receivers, message.as_string())
            smtp_obj.quit()
            return True
        except Exception as e:
            log.error(f"发送邮件失败: {e}")
            return False

    def _send_telegram(self, config, title, content):
        """发送Telegram推送"""
        bot_token = config['bot_token']
        chat_id = config['chat_id']
        # Telegram支持Markdown
        text = f"<b>{title}</b>\n\n{content}\n\n<i>FeedGrep RSS推送服务</i>"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        return response.status_code == 200

    def send_bulk_push(self, channels, title, content):
        """
        批量发送推送消息
        
        Args:
            channels: 渠道名称列表
            title: 消息标题
            content: 消息内容
        """
        success_count = 0
        for channel in channels:
            if self.send_push(channel, title, content):
                success_count += 1
        return success_count