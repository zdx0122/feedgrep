#!/bin/bash

# FeedGrep 服务管理脚本
# 用法: ./feedgrep.sh {start|stop|restart}

# 定义变量
APP_NAME="FeedGrep"
PID_FILE="/tmp/feedgrep.pid"
LOG_FILE="/tmp/feedgrep.log"

# 检查是否在 Windows Git Bash 环境下运行
if [[ $OSTYPE == "msys" ]] || [[ $OSTYPE == "win32" ]]; then
    IS_WINDOWS=1
else
    IS_WINDOWS=0
fi

# 输出带颜色的信息
print_status() {
    if [[ $IS_WINDOWS -eq 1 ]]; then
        echo "$1"
    else
        case "$1" in
            *"启动"*|*"开始"*|*"running"*|*"started"*)
                echo -e "\033[32m$1\033[0m"  # 绿色
                ;;
            *"停止"*|*"终止"*|*"stopped"*)
                echo -e "\033[33m$1\033[0m"  # 黄色
                ;;
            *"错误"*|*"失败"*|*"error"*|*"failed"*)
                echo -e "\033[31m$1\033[0m"  # 红色
                ;;
            *)
                echo "$1"
                ;;
        esac
    fi
}

# 检查服务是否正在运行
is_running() {
    if [[ -f $PID_FILE ]]; then
        local pid=$(cat $PID_FILE)
        if ps -p $pid > /dev/null 2>&1; then
            return 0  # 正在运行
        else
            rm -f $PID_FILE  # 清理旧的 PID 文件
            return 1  # 没有运行
        fi
    else
        # 在 Windows 上使用不同的检查方法
        if [[ $IS_WINDOWS -eq 1 ]]; then
            if pgrep -f "python.*feedgrep.py" > /dev/null 2>&1; then
                return 0
            else
                return 1
            fi
        fi
        return 1  # 没有运行
    fi
}

# 获取运行中的进程 PID
get_pid() {
    if [[ -f $PID_FILE ]]; then
        cat $PID_FILE
    else
        # 在 Windows 上查找进程
        if [[ $IS_WINDOWS -eq 1 ]]; then
            pgrep -f "python.*feedgrep.py" 2>/dev/null
        fi
    fi
}

# 启动服务
start() {
    if is_running; then
        local pid=$(get_pid)
        print_status "警告: $APP_NAME 已经在运行中 (PID: $pid)"
        return 1
    fi
    
    print_status "正在启动 $APP_NAME..."
    
    # 切换到脚本所在目录
    cd "$(dirname "$0")"
    
    # 检查必要文件是否存在
    if [[ ! -f "feedgrep.py" ]]; then
        print_status "错误: 找不到 feedgrep.py 文件"
        return 1
    fi
    
    # 启动服务
    if [[ $IS_WINDOWS -eq 1 ]]; then
        # Windows 下启动方式
        python feedgrep.py > "$LOG_FILE" 2>&1 &
        local pid=$!
        echo $pid > $PID_FILE
    else
        # Unix/Linux 下启动方式
        nohup python3 feedgrep.py > "$LOG_FILE" 2>&1 &
        local pid=$!
        echo $pid > $PID_FILE
    fi
    
    # 等待一下确认进程启动
    sleep 2
    
    if ps -p $pid > /dev/null 2>&1; then
        print_status "$APP_NAME 已成功启动 (PID: $pid)"
        return 0
    else
        print_status "错误: $APP_NAME 启动失败，请查看日志文件 $LOG_FILE"
        rm -f $PID_FILE
        return 1
    fi
}

# 停止服务
stop() {
    if ! is_running; then
        print_status "警告: $APP_NAME 没有在运行"
        return 1
    fi
    
    print_status "正在停止 $APP_NAME..."
    
    local pid=$(get_pid)
    
    # 尝试优雅地停止进程
    if [[ -n $pid ]]; then
        kill $pid > /dev/null 2>&1
        
        # 等待进程结束
        local count=0
        while ps -p $pid > /dev/null 2>&1; do
            sleep 1
            count=$((count + 1))
            if [[ $count -gt 10 ]]; then
                # 强制杀死进程
                kill -9 $pid > /dev/null 2>&1
                break
            fi
        done
    fi
    
    # 清理 PID 文件
    rm -f $PID_FILE
    
    print_status "$APP_NAME 已停止"
    return 0
}

# 重启服务
restart() {
    print_status "正在重启 $APP_NAME..."
    stop
    # 等待一会儿确保进程完全停止
    sleep 3
    start
}

# 显示使用方法
usage() {
    echo "用法: $0 {start|stop|restart}"
    echo ""
    echo "命令:"
    echo "  start   - 启动 $APP_NAME 服务"
    echo "  stop    - 停止 $APP_NAME 服务"
    echo "  restart - 重启 $APP_NAME 服务"
    echo ""
}

# 主程序入口
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    *)
        usage
        exit 1
        ;;
esac

exit $?