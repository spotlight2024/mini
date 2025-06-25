#!/bin/bash

# 日志查看脚本
# 使用方法: ./shell/view_logs.sh [选项]

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$WORK_DIR/logs"

# 显示帮助信息
show_help() {
    echo "日志查看工具"
    echo ""
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -f, --follow     实时跟踪最新日志"
    echo "  -l, --latest     显示最新日志文件的最后100行"
    echo "  -a, --all        显示所有日志文件"
    echo "  -e, --error      只显示错误日志"
    echo "  -t, --today      显示今天的日志"
    echo "  -n <行数>        显示指定行数 (默认100)"
    echo "  -h, --help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -f              # 实时跟踪日志"
    echo "  $0 -l -n 50        # 显示最新日志的最后50行"
    echo "  $0 -e              # 只显示错误日志"
    echo "  $0 -t              # 显示今天的日志"
}

# 获取最新日志文件
get_latest_log() {
    ls -t "$LOG_DIR"/service_*.log 2>/dev/null | head -1
}

# 检查日志目录
if [ ! -d "$LOG_DIR" ]; then
    echo "❌ 日志目录不存在: $LOG_DIR"
    exit 1
fi

# 解析参数
FOLLOW=false
LATEST=false
ALL=false
ERROR_ONLY=false
TODAY=false
LINES=100

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -l|--latest)
            LATEST=true
            shift
            ;;
        -a|--all)
            ALL=true
            shift
            ;;
        -e|--error)
            ERROR_ONLY=true
            shift
            ;;
        -t|--today)
            TODAY=true
            shift
            ;;
        -n)
            LINES="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 如果没有指定选项，默认显示最新日志
if [ "$FOLLOW" = false ] && [ "$LATEST" = false ] && [ "$ALL" = false ] && [ "$ERROR_ONLY" = false ] && [ "$TODAY" = false ]; then
    LATEST=true
fi

# 实时跟踪日志
if [ "$FOLLOW" = true ]; then
    LATEST_LOG=$(get_latest_log)
    if [ -n "$LATEST_LOG" ]; then
        echo "正在实时跟踪日志: $LATEST_LOG"
        echo "按 Ctrl+C 停止跟踪"
        echo "----------------------------------------"
        tail -f "$LATEST_LOG"
    else
        echo "❌ 未找到日志文件"
        exit 1
    fi
    exit 0
fi

# 显示最新日志
if [ "$LATEST" = true ]; then
    LATEST_LOG=$(get_latest_log)
    if [ -n "$LATEST_LOG" ]; then
        echo "显示最新日志的最后 $LINES 行: $LATEST_LOG"
        echo "----------------------------------------"
        tail -n "$LINES" "$LATEST_LOG"
    else
        echo "❌ 未找到日志文件"
        exit 1
    fi
    exit 0
fi

# 显示所有日志文件
if [ "$ALL" = true ]; then
    echo "所有日志文件:"
    echo "----------------------------------------"
    for log_file in "$LOG_DIR"/service_*.log; do
        if [ -f "$log_file" ]; then
            echo "文件: $log_file"
            echo "大小: $(du -h "$log_file" | cut -f1)"
            echo "最后修改: $(stat -c %y "$log_file")"
            echo "----------------------------------------"
        fi
    done
    exit 0
fi

# 只显示错误日志
if [ "$ERROR_ONLY" = true ]; then
    LATEST_LOG=$(get_latest_log)
    if [ -n "$LATEST_LOG" ]; then
        echo "显示错误日志: $LATEST_LOG"
        echo "----------------------------------------"
        grep -i "error\|exception\|traceback\|failed" "$LATEST_LOG" | tail -n "$LINES"
    else
        echo "❌ 未找到日志文件"
        exit 1
    fi
    exit 0
fi

# 显示今天的日志
if [ "$TODAY" = true ]; then
    TODAY_DATE=$(date +%Y%m%d)
    TODAY_LOG="$LOG_DIR/service_${TODAY_DATE}_*.log"
    
    if ls $TODAY_LOG >/dev/null 2>&1; then
        echo "显示今天的日志:"
        echo "----------------------------------------"
        for log_file in $TODAY_LOG; do
            if [ -f "$log_file" ]; then
                echo "文件: $log_file"
                echo "----------------------------------------"
                tail -n "$LINES" "$log_file"
                echo ""
            fi
        done
    else
        echo "❌ 未找到今天的日志文件"
        exit 1
    fi
    exit 0
fi 