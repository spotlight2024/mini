#!/bin/bash

# 完全动态生成Chrome代理扩展
# 支持通过参数传递代理配置

set -e

echo "=== 动态生成Chrome代理扩展 ==="

# 函数：显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --host HOST         代理服务器地址 (必需)"
    echo "  -p, --port PORT         代理服务器端口 (必需)"
    echo "  -u, --username USER     代理用户名 (可选)"
    echo "  -w, --password PASS     代理密码 (可选)"
    echo "  -e, --enabled BOOL      是否启用代理 (默认: true)"
    echo "  -d, --dir DIR           扩展目录 (默认: /opt/chrome_extensions/proxy_auth)"
    echo "  --help                  显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -h 61.132.231.167 -p 57001 -u vgmpgv -w 1bk79g9y"
    echo "  $0 --host 61.132.231.167 --port 57001 --enabled false"
    echo ""
}

# 函数：生成manifest.json
generate_manifest() {
    local extension_dir="$1"
    
    cat > "$extension_dir/manifest.json" << 'EOF'
{
  "manifest_version": 3,
  "name": "Auto Proxy Auth",
  "version": "1.0",
  "description": "Automatically authenticate HTTP proxy without popup dialogs",
  "permissions": [
    "proxy",
    "webRequest",
    "webRequestAuthProvider"
  ],
  "host_permissions": [
    "<all_urls>"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "web_accessible_resources": [
    {
      "resources": ["proxy_config.json"],
      "matches": ["<all_urls>"]
    }
  ]
}
EOF
    echo "✓ manifest.json 已生成"
}

# 函数：生成background.js
generate_background_js() {
    local extension_dir="$1"
    local proxy_host="$2"
    local proxy_port="$3"
    local proxy_username="$4"
    local proxy_password="$5"
    local proxy_enabled="$6"
    
    cat > "$extension_dir/background.js" << EOF
// 动态生成的代理配置
let proxyConfig = {
  host: '$proxy_host',
  port: '$proxy_port',
  username: '$proxy_username',
  password: '$proxy_password',
  enabled: $proxy_enabled
};

// 从配置文件读取代理设置（备用方案）
async function loadProxyConfigFromFile() {
  try {
    const response = await fetch(chrome.runtime.getURL('proxy_config.json'));
    if (response.ok) {
      const config = await response.json();
      // 如果配置文件存在且有效，则使用配置文件
      if (config.host && config.port) {
        proxyConfig = {
          host: config.host || proxyConfig.host,
          port: config.port || proxyConfig.port,
          username: config.username || proxyConfig.username,
          password: config.password || proxyConfig.password,
          enabled: config.enabled !== undefined ? config.enabled : proxyConfig.enabled
        };
      }
    }
  } catch (error) {
    console.log('Using inline proxy config');
  }
  
  console.log('Proxy config loaded:', {
    host: proxyConfig.host,
    port: proxyConfig.port,
    username: proxyConfig.username ? '[SET]' : '[NOT SET]',
    password: proxyConfig.password ? '[SET]' : '[NOT SET]',
    enabled: proxyConfig.enabled
  });
  
  if (proxyConfig.enabled && proxyConfig.host && proxyConfig.port) {
    console.log('Setting up proxy with authentication...');
    updateProxySettings();
  } else {
    console.log('Proxy not enabled or incomplete configuration');
  }
}

// 更新Chrome代理设置
function updateProxySettings() {
  if (!proxyConfig.enabled || !proxyConfig.host || !proxyConfig.port) {
    // 禁用代理或配置不完整
    chrome.proxy.settings.set({
      value: {mode: "direct"},
      scope: 'regular'
    });
    return;
  }

  const config = {
    mode: "fixed_servers",
    rules: {
      singleProxy: {
        scheme: "http",
        host: proxyConfig.host,
        port: parseInt(proxyConfig.port)
      }
    }
  };

  chrome.proxy.settings.set({
    value: config,
    scope: 'regular'
  }, () => {
    if (chrome.runtime.lastError) {
      console.error('Failed to set proxy:', chrome.runtime.lastError);
    } else {
      console.log('Proxy set successfully:', config);
    }
  });
}

// 处理代理认证
chrome.webRequest.onAuthRequired.addListener(
  function(details) {
    console.log('Auth required for:', details.url, 'isProxy:', details.isProxy);
    
    // 检查是否是代理认证请求
    if (details.isProxy && proxyConfig.enabled && proxyConfig.username && proxyConfig.password) {
      console.log('Providing proxy authentication - Username:', proxyConfig.username);
      return {
        authCredentials: {
          username: proxyConfig.username,
          password: proxyConfig.password
        }
      };
    }
    
    // 如果不是代理认证或配置不完整，返回空对象
    console.log('Auth request ignored - not proxy or config incomplete');
    return {};
  },
  {urls: ["<all_urls>"]},
  ["blocking"]
);

// 插件启动时初始化
chrome.runtime.onStartup.addListener(async () => {
  console.log('Auto Proxy Auth extension started');
  await loadProxyConfigFromFile();
});

chrome.runtime.onInstalled.addListener(async () => {
  console.log('Auto Proxy Auth extension installed');
  await loadProxyConfigFromFile();
});

// 立即执行配置加载
loadProxyConfigFromFile();
EOF
    echo "✓ background.js 已生成"
}

# 函数：生成proxy_config.json（备用配置）
generate_proxy_config() {
    local extension_dir="$1"
    local proxy_host="$2"
    local proxy_port="$3"
    local proxy_username="$4"
    local proxy_password="$5"
    local proxy_enabled="$6"
    
    cat > "$extension_dir/proxy_config.json" << EOF
{
  "host": "$proxy_host",
  "port": "$proxy_port",
  "username": "$proxy_username",
  "password": "$proxy_password",
  "enabled": $proxy_enabled
}
EOF
    echo "✓ proxy_config.json 已生成"
}

# 函数：设置文件权限
set_permissions() {
    local extension_dir="$1"
    
    chmod 644 "$extension_dir"/*
    chown -R 1200:1200 "$extension_dir" 2>/dev/null || true
    echo "✓ 文件权限已设置"
}

# 主函数：生成完整的Chrome扩展
generate_extension() {
    local extension_dir="$1"
    local proxy_host="$2"
    local proxy_port="$3"
    local proxy_username="$4"
    local proxy_password="$5"
    local proxy_enabled="$6"
    
    echo "生成Chrome代理扩展到: $extension_dir"
    echo "代理配置:"
    echo "  主机: $proxy_host"
    echo "  端口: $proxy_port"
    echo "  用户名: $proxy_username"
    echo "  密码: [已设置]"
    echo "  启用: $proxy_enabled"
    echo ""
    
    # 创建目录
    mkdir -p "$extension_dir"
    
    # 生成所有文件
    generate_manifest "$extension_dir"
    generate_background_js "$extension_dir" "$proxy_host" "$proxy_port" "$proxy_username" "$proxy_password" "$proxy_enabled"
    generate_proxy_config "$extension_dir" "$proxy_host" "$proxy_port" "$proxy_username" "$proxy_password" "$proxy_enabled"
    set_permissions "$extension_dir"
    
    echo ""
    echo "✅ Chrome代理扩展生成完成"
    echo "扩展路径: $extension_dir"
    echo "Chrome启动参数: --load-extension=$extension_dir"
}

# 解析命令行参数
parse_arguments() {
    local proxy_host=""
    local proxy_port=""
    local proxy_username=""
    local proxy_password=""
    local proxy_enabled="true"
    local extension_dir="/opt/chrome_extensions/proxy_auth"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--host)
                proxy_host="$2"
                shift 2
                ;;
            -p|--port)
                proxy_port="$2"
                shift 2
                ;;
            -u|--username)
                proxy_username="$2"
                shift 2
                ;;
            -w|--password)
                proxy_password="$2"
                shift 2
                ;;
            -e|--enabled)
                proxy_enabled="$2"
                shift 2
                ;;
            -d|--dir)
                extension_dir="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                echo "错误: 未知参数 $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # 验证必需参数
    if [[ -z "$proxy_host" || -z "$proxy_port" ]]; then
        echo "错误: 代理主机和端口是必需的"
        show_usage
        exit 1
    fi
    
    # 验证布尔值
    if [[ "$proxy_enabled" != "true" && "$proxy_enabled" != "false" ]]; then
        echo "错误: enabled 参数必须是 true 或 false"
        exit 1
    fi
    
    # 返回参数
    echo "$extension_dir|$proxy_host|$proxy_port|$proxy_username|$proxy_password|$proxy_enabled"
}

# 主程序
main() {
    # 检查是否有参数
    if [[ $# -eq 0 ]]; then
        # 如果没有参数，尝试从环境变量读取
        local proxy_host="${PROXY_HOST:-}"
        local proxy_port="${PROXY_PORT:-}"
        local proxy_username="${PROXY_USERNAME:-}"
        local proxy_password="${PROXY_PASSWORD:-}"
        local proxy_enabled="${PROXY_ENABLED:-true}"
        local extension_dir="/opt/chrome_extensions/proxy_auth"
        
        if [[ -z "$proxy_host" || -z "$proxy_port" ]]; then
            echo "错误: 环境变量 PROXY_HOST 和 PROXY_PORT 未设置"
            echo "请使用命令行参数或设置环境变量"
            show_usage
            exit 1
        fi
        
        echo "从环境变量读取配置..."
        generate_extension "$extension_dir" "$proxy_host" "$proxy_port" "$proxy_username" "$proxy_password" "$proxy_enabled"
    else
        # 解析命令行参数
        local args=$(parse_arguments "$@")
        IFS='|' read -r extension_dir proxy_host proxy_port proxy_username proxy_password proxy_enabled <<< "$args"
        
        generate_extension "$extension_dir" "$proxy_host" "$proxy_port" "$proxy_username" "$proxy_password" "$proxy_enabled"
    fi
}

# 执行主程序
main "$@"
