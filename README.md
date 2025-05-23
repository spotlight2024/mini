# spotium
## 项目介绍

在云服务上跑多个 android 虚拟机，用户指令帮我点一杯咖啡，我可以操作微信小程序，帮用户在服务器上的虚拟机打开微信小程序，实现操作

定义概念：
1. 云服务器，一个 Linux 的远程服务器
2. android 虚拟机：一个 google 的 android 模拟器
3. 脚本（script）：通过脚本使用 webdriver 去连接，虚拟机里面的微信小程序的 webview，脚本会运行在云服务器上。
4. APP：安装在虚拟机上的 android app，用户指令会发送到这个 app，app 通过发送命令到脚本，脚本执行真正的 web 操作。

技术架构：
1. 一个云服务器，上面跑多个android 虚拟机
2. 脚本通过 webdriver 连接微信小程序，实现模拟操作
3. 虚拟机上会有一个 app，这个 app 用来和脚本交互，用户指令发送到这个 app，app 调用脚本连接，脚本逻辑要简单不要有业务逻辑，尽量只负责连接 web。
4. 整体方案，需要能够快速部署和方便管理
流程：
用户指令 -> APP ->  script -> selenuim driver -> 小程序 webview

技术选型和模块
项目结构
spotium/
├── app/             # Android APP 源码
├── script/          # Python 脚本服务
│   ├── main.py      # 服务入口
│   ├── webdriver/   # WebDriver 相关代码
│   ├── server/      # 和客户端 APP 通信代码
│   └── requirements.txt
├── docs/            # 项目文档
├── docker/          # Dockerfile、docker-compose.yml
└── README.md        # 项目说明文件

客户端：android 代码
- 通过 http 请求和脚本通信，接口协议见 

script：
  - 使用 python，可以部署到云服务器，作为 server 和客户端通信。APP 通过 http 请求，和脚本通信
  - 使用 selenium 通过 webdriver 连接 微信小程序
  - 

- 主要模块和职责
- ** app/ **  手机上运行的 android app 的代码

- **script/**  脚本代码，脚本运行在云服务器上，可接受多个 app 客户端的请求，需要维护对一个的 app 设备
  - ** driver.py** , 驱动的能力层，调用 driver 的真正实现类
    - web_driver.py, webdriver 的实现类，使用  @selenuim 实现，设计时考虑可以替换 selenuim 的实现
  - ** server.py ** ,提供 HTTP 服务，处理客户端的逻辑，接口见 @接口协议
    - connect,通过 web_driver 去连接
    - action， 根据 type 去调用 web_driver
  - ** device.py ** 维护对应的 app client 信息
    - 包含 ip端口号，等，可支持扩展
  - 整个脚本需要支持 命令行 CLI 的方式调用
  - **tests** 测试代码

接口协议
- POST /connect 
连接 webview
请求：{ serier_id, ... }

响应：{ code: "success" | "fail", message: "xxx" }

- POST /action
通过 webview 去执行操作
请求：{ type:"", ... }
# type :
    click,findElement

响应：{ code: "success" | "fail", message: "xxx" }
- POST /findElement


## 测试说明

### 1. 安装依赖

```bash
pip install -r script/requirements.txt
pip install pytest
```

### 2. 运行所有单元测试

在项目根目录下执行：

```bash
PYTHONPATH=script pytest script/tests/
```

### 3. 运行指定测试用例

例如只运行真实连接测试：

```bash
PYTHONPATH=script pytest script/tests/test_web_driver.py -k test_real_connect
```

### 4. 显示 print/logging 日志

加 `-s` 参数显示 print 日志：

```bash
PYTHONPATH=script pytest script/tests/ -s
```

加 `--log-cli-level=INFO` 显示 logging 日志：

```bash
PYTHONPATH=script pytest script/tests/ --log-cli-level=INFO
```

### 5. 注意事项
- 真实连接测试（如 `test_real_connect`）需要本地有可用的 Chrome/Chromium 并开启了 9222 端口。
- 推荐将所有测试代码放在 `script/tests/` 目录，便于管理和自动化。
