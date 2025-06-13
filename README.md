spotium
项目介绍

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

暂时无法在飞书文档外展示此内容
客户端：android 代码
- 通过 http 请求和脚本通信，接口协议见 

script：
  - 使用 python，可以部署到云服务器，作为 server 和客户端通信。APP 通过 http 请求，和脚本通信
  - 使用 selenium 通过 webdriver 连接 微信小程序

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

手机 ADB 连接

# 获取当前 activity
adb shell dumpsys activity top | grep ACTIVITY

# 获取进程
adb shell ps | grep tencent


adb shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'



测试说明
1. 安装依赖

pip install -r script/requirements.txt
pip install pytest

2. 运行所有单元测试

在项目根目录下执行：

PYTHONPATH=script pytest script/tests/

3. 运行指定测试用例

例如只运行真实连接测试：

PYTHONPATH=script pytest script/tests/test_web_driver.py -k test_real_connect

4. 显示 print/logging 日志

加 -s 参数显示 print 日志：

PYTHONPATH=script pytest script/tests/ -s

加 --log-cli-level=INFO 显示 logging 日志：

PYTHONPATH=script pytest script/tests/ --log-cli-level=INFO

5. 注意事项
- 真实连接测试（如 test_real_connect）需要本地有可用的 Chrome/Chromium 并开启了 9222 端口。
- 推荐将所有测试代码放在 script/tests/ 目录，便于管理和自动化。


优化

您的整体架构已经非常专业，具备高扩展性和良好的解耦能力。下面我从**资源管理、健壮性、可维护性、可扩展性、性能与安全**等角度，结合您的业务场景，给出进一步的优化建议：


---

一、资源管理与回收

1. WebDriver 实例泄漏与内存占用

问题：  
- 当前 DevicePool 中的 AndroidDevice 及其 WebDriver 实例只要未手动 disconnect，就会一直常驻内存。
- 如果有大量虚拟机连接但长时间不活跃，WebDriver 实例会持续增加，导致内存和句柄泄漏，最终影响服务稳定性。

优化建议：
- 空闲超时回收机制：为每个 AndroidDevice 增加 last_active_time 字段，定期扫描 pool，自动断开和清理长时间未活跃的设备及其 WebDriver 实例。
- 最大连接数限制：为 pool 设置最大容量，超出时拒绝新连接或优先回收最久未用的连接（LRU）。
- 定期健康检查：定时检测 WebDriver/adb 连接是否可用，不可用时自动回收。

伪代码示例：
import time

class AndroidDevice:
    def __init__(...):
        ...
        self.last_active_time = time.time()

    def touch(self):
        self.last_active_time = time.time()

class DevicePool:
    def cleanup(self, timeout=1800):
        now = time.time()
        to_remove = []
        for serial_id, device in self.pool.items():
            if now - device.last_active_time > timeout:
                device.disconnect()
                to_remove.append(serial_id)
        for serial_id in to_remove:
            del self.pool[serial_id]
- 可用定时任务或后台线程定期调用 cleanup()。


---

二、健壮性与异常处理

1. 连接异常与自动重连

- WebDriver/adb 连接断开时自动重连，避免因偶发网络或设备异常导致服务不可用。
- 异常兜底：所有接口和核心方法应有异常捕获和详细日志，便于线上问题定位。

2. 连接状态监控

- 提供 /status 或 /health 接口，实时监控各虚拟机连接状态，便于运维和自动化监控。


---

三、可维护性与扩展性

1. 配置与依赖解耦

- WebDriver 实现类、连接参数、超时等建议全部配置化，便于多环境部署和动态切换。
- 支持通过环境变量或配置文件切换 WebDriver 实现，无需改动代码。

2. 业务与驱动解耦

- 业务层只依赖接口，所有驱动实现都可热插拔，便于未来支持更多自动化框架。

3. 日志与审计

- 关键操作（连接、断开、异常、回收等）都应有详细日志，便于追踪和审计。


---

四、性能与并发

1. 并发安全

- 当前已用线程锁，适合多线程场景。若后续用协程（如 FastAPI 的 async），可考虑用异步锁或队列。

2. 进程/分布式扩展

- 单机 pool 适合单进程。若需多进程/多节点部署，建议 pool 状态持久化到 Redis/数据库，实现分布式资源管理。


---

五、安全性

1. 权限与认证

- 所有接口建议加认证（如 token/session 校验），防止未授权访问。
- 对敏感操作（如 disconnect、action）做权限校验。

2. 参数校验与防注入

- 所有外部参数（如 selector、method）都应严格校验，防止注入攻击。


---

六、接口与协议

1. 错误码与响应规范

- 统一接口响应格式，区分业务错误与系统错误，便于前后端协作和自动化处理。

2. OpenAPI/Swagger 文档

- 保持接口文档与实现同步，便于团队协作和自动化测试。


---

七、可测试性

- 为核心模块（DevicePool、AndroidDevice、WebDriver 实现）编写单元测试，保证重构和扩展时的稳定性。
- 可用 mock WebDriver 实现做自动化测试。


---

八、总结与建议

重点优化方向
1. 资源自动回收（防止 WebDriver 泄漏）
2. 连接健康检查与自动重连
3. 配置化与依赖解耦
4. 接口安全与参数校验
5. 分布式/多进程扩展能力（如有需求）
