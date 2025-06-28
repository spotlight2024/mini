# ACTION_COLLECT_ITEM_INFO 协议优化实施计划

## 项目概述

本计划旨在通过渐进式优化，提升 `ACTION_COLLECT_ITEM_INFO` 协议的易用性、可读性和可维护性，同时保持向后兼容性。

## 目标

1. **提升可读性**：将复杂的命令行语法转换为结构化的JSON配置
2. **增强可维护性**：支持配置模板化和版本控制
3. **改善错误处理**：提供更友好的错误信息和调试建议
4. **保持兼容性**：确保现有配置继续正常工作
5. **提升开发效率**：减少配置错误，支持配置复用

## 实施阶段

### 阶段一：基础架构准备（1-2周）

#### 1.1 解析器重构
- [ ] 重构现有命令解析器，支持JSON配置
- [ ] 实现配置验证机制
- [ ] 添加配置缓存功能

**代码示例：**
```kotlin
// 新增JSON配置解析器
class JsonConfigParser {
    fun parse(configJson: String): CollectConfig {
        return GsonUtils.gson.fromJson(configJson, CollectConfig::class.java)
    }
    
    fun validate(config: CollectConfig): ValidationResult {
        // 验证配置有效性
    }
}

// 配置数据结构
data class CollectConfig(
    val container: ContainerConfig,
    val options: OptionsConfig,
    val fields: Map<String, FieldConfig>
)
```

#### 1.2 向后兼容层
- [ ] 实现旧格式到新格式的自动转换
- [ ] 保持现有API接口不变
- [ ] 添加兼容性测试

**代码示例：**
```kotlin
class LegacyCompatibilityLayer {
    fun convertLegacyCommand(command: String): CollectConfig {
        // 解析旧格式命令
        val parts = command.split(" ")
        val config = CollectConfig()
        
        // 转换参数
        for (part in parts) {
            when {
                part.startsWith("--id=") -> config.container.selector = part.substring(5)
                part.startsWith("--pkg=") -> config.options.package = part.substring(6)
                // ... 其他参数转换
            }
        }
        
        return config
    }
}
```

#### 1.3 配置管理
- [ ] 实现配置文件加载机制
- [ ] 支持配置文件热重载
- [ ] 添加配置版本控制

### 阶段二：核心功能实现（2-3周）

#### 2.1 JSON配置支持
- [ ] 实现完整的JSON配置解析
- [ ] 支持嵌套字段定义
- [ ] 实现字段类型验证

**实现要点：**
```kotlin
// 字段配置支持
data class FieldConfig(
    val selector: String,
    val type: FieldType = FieldType.TEXT,
    val regex: String? = null,
    val required: Boolean = false,
    val fallback: String? = null,
    val fields: Map<String, FieldConfig>? = null // 用于数组类型
)

enum class FieldType {
    TEXT, ATTRIBUTE, CHECKED, ARRAY, IMAGE, OCR, LLM
}
```

#### 2.2 模板系统
- [ ] 实现配置模板定义
- [ ] 支持模板继承和覆盖
- [ ] 添加模板验证机制

**模板示例：**
```json
{
  "templates": {
    "base_shop": {
      "options": {
        "close_dialog": true,
        "package": "com.lucky.luckyclient",
        "loading_view": "com.lucky.luckyclient:id/v_lottie"
      }
    },
    "shop_list": {
      "extends": "base_shop",
      "container": "com.lucky.luckyclient:id/recycler_view",
      "fields": {
        "name": "com.lucky.luckyclient:id/tv_dept_name",
        "location": "com.lucky.luckyclient:id/tv_dept_address"
      }
    }
  }
}
```

#### 2.3 错误处理优化
- [ ] 实现结构化错误信息
- [ ] 添加错误分类和代码
- [ ] 提供调试建议

**错误处理示例：**
```kotlin
sealed class CollectError {
    data class MissingField(
        val field: String,
        val selector: String,
        val suggestions: List<String>
    ) : CollectError()
    
    data class InvalidSelector(
        val selector: String,
        val reason: String,
        val alternatives: List<String>
    ) : CollectError()
    
    data class Timeout(
        val operation: String,
        val duration: Long,
        val context: Map<String, Any>
    ) : CollectError()
}
```

### 阶段三：高级功能（2-3周）

#### 3.1 智能重试机制
- [ ] 实现指数退避重试
- [ ] 支持条件重试
- [ ] 添加重试统计

**重试配置：**
```json
{
  "retry": {
    "max_attempts": 3,
    "backoff": "exponential",
    "base_delay": 1000,
    "max_delay": 10000,
    "conditions": ["element_not_found", "timeout", "network_error"]
  }
}
```

#### 3.2 性能优化
- [ ] 实现配置缓存
- [ ] 支持批量操作
- [ ] 添加性能监控

**缓存配置：**
```json
{
  "cache": {
    "enabled": true,
    "ttl": 3600,
    "key_pattern": "config_{hash}",
    "max_size": 1000
  }
}
```

#### 3.3 调试工具
- [ ] 实现配置验证工具
- [ ] 添加调试模式
- [ ] 支持配置对比

### 阶段四：迁移和优化（1-2周）

#### 4.1 自动迁移工具
- [ ] 开发配置转换工具
- [ ] 实现批量迁移脚本
- [ ] 添加迁移验证

**迁移工具示例：**
```python
#!/usr/bin/env python3
import json
import re
import sys

def convert_legacy_config(legacy_command):
    """将旧格式命令转换为新格式"""
    
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {},
            "options": {},
            "filters": {}
        },
        "fields": {}
    }
    
    # 解析参数
    parts = legacy_command.split()
    for part in parts:
        if part.startswith("--"):
            key, value = part[2:].split("=", 1)
            if key == "id":
                config["config"]["container"]["selector"] = value
            elif key == "pkg":
                config["config"]["options"]["package"] = value
            elif key == "close_dialog":
                config["config"]["options"]["close_dialog"] = value == "1"
            elif key == "singleton":
                config["config"]["options"]["singleton"] = value == "1"
            elif key == "important_fields":
                config["config"]["filters"]["required_fields"] = value.split(",")
    
    # 解析字段
    field_part = parts[-1]
    for field_def in field_part.split(","):
        if "=" in field_def:
            field_name, selector = field_def.split("=", 1)
            config["fields"][field_name] = {
                "selector": selector,
                "type": "text"
            }
    
    return config

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_config.py <legacy_command>")
        sys.exit(1)
    
    legacy_command = sys.argv[1]
    new_config = convert_legacy_config(legacy_command)
    print(json.dumps(new_config, indent=2))
```

#### 4.2 文档和培训
- [ ] 更新API文档
- [ ] 创建使用示例
- [ ] 提供培训材料

#### 4.3 测试和验证
- [ ] 完善单元测试
- [ ] 添加集成测试
- [ ] 进行性能测试

## 技术实现细节

### 1. 配置解析器设计

```kotlin
interface ConfigParser {
    fun parse(input: String): CollectConfig
    fun validate(config: CollectConfig): ValidationResult
    fun convertLegacy(command: String): CollectConfig
}

class JsonConfigParser : ConfigParser {
    override fun parse(input: String): CollectConfig {
        return try {
            GsonUtils.gson.fromJson(input, CollectConfig::class.java)
        } catch (e: Exception) {
            throw ConfigParseException("Failed to parse JSON config", e)
        }
    }
    
    override fun validate(config: CollectConfig): ValidationResult {
        val errors = mutableListOf<String>()
        
        // 验证容器配置
        if (config.container.selector.isBlank()) {
            errors.add("Container selector is required")
        }
        
        // 验证字段配置
        if (config.fields.isEmpty()) {
            errors.add("At least one field must be defined")
        }
        
        return ValidationResult(errors.isEmpty(), errors)
    }
}
```

### 2. 模板系统实现

```kotlin
class TemplateManager {
    private val templates = mutableMapOf<String, CollectConfig>()
    
    fun loadTemplates(templateFile: String) {
        val templateData = File(templateFile).readText()
        val templateConfig = GsonUtils.gson.fromJson(templateData, TemplateConfig::class.java)
        
        for ((name, template) in templateConfig.templates) {
            templates[name] = resolveTemplate(template)
        }
    }
    
    fun getTemplate(name: String): CollectConfig? {
        return templates[name]
    }
    
    private fun resolveTemplate(template: TemplateConfig): CollectConfig {
        val config = CollectConfig()
        
        // 处理继承
        if (template.extends != null) {
            val parent = templates[template.extends]
            if (parent != null) {
                config.merge(parent)
            }
        }
        
        // 应用当前模板
        config.merge(template)
        
        return config
    }
}
```

### 3. 错误处理机制

```kotlin
class ErrorHandler {
    fun handleError(error: CollectError): CommandResult {
        return when (error) {
            is CollectError.MissingField -> {
                val message = buildString {
                    append("Required field '${error.field}' not found")
                    append("\nSelector: ${error.selector}")
                    if (error.suggestions.isNotEmpty()) {
                        append("\nSuggestions:")
                        error.suggestions.forEach { append("\n- $it") }
                    }
                }
                CommandResult.failure(CommandResult.CODE_NO_ITEM, message)
            }
            
            is CollectError.InvalidSelector -> {
                val message = buildString {
                    append("Invalid selector: ${error.selector}")
                    append("\nReason: ${error.reason}")
                    if (error.alternatives.isNotEmpty()) {
                        append("\nAlternatives:")
                        error.alternatives.forEach { append("\n- $it") }
                    }
                }
                CommandResult.failure(CommandResult.CODE_ILLEGAL_ARGUMENT, message)
            }
            
            is CollectError.Timeout -> {
                val message = "Operation '${error.operation}' timed out after ${error.duration}ms"
                CommandResult.failure(CommandResult.CODE_OPERATION_TIMEOUT, message)
            }
        }
    }
}
```

## 风险评估和缓解措施

### 1. 兼容性风险
- **风险**: 现有配置可能失效
- **缓解**: 
  - 保持完整的向后兼容性
  - 提供自动迁移工具
  - 分阶段部署，先支持新格式，再逐步迁移

### 2. 性能风险
- **风险**: JSON解析可能影响性能
- **缓解**:
  - 实现配置缓存
  - 优化解析算法
  - 添加性能监控

### 3. 学习成本
- **风险**: 团队需要学习新语法
- **缓解**:
  - 提供详细文档和示例
  - 创建培训材料
  - 提供迁移工具和指导

## 成功指标

### 1. 功能指标
- [ ] 100%向后兼容性
- [ ] 支持所有现有功能
- [ ] 新增JSON配置支持
- [ ] 实现模板系统

### 2. 性能指标
- [ ] 配置解析时间 < 10ms
- [ ] 内存使用增加 < 20%
- [ ] 错误处理响应时间 < 100ms

### 3. 用户体验指标
- [ ] 配置错误减少 50%
- [ ] 调试时间减少 30%
- [ ] 配置维护时间减少 40%

## 时间安排

| 阶段 | 时间 | 主要任务 | 交付物 |
|------|------|----------|--------|
| 阶段一 | 1-2周 | 基础架构准备 | 解析器重构、兼容层 |
| 阶段二 | 2-3周 | 核心功能实现 | JSON配置、模板系统 |
| 阶段三 | 2-3周 | 高级功能 | 重试机制、性能优化 |
| 阶段四 | 1-2周 | 迁移优化 | 迁移工具、文档 |

## 总结

本实施计划通过渐进式优化，在保持向后兼容的前提下，显著提升协议的易用性和可维护性。关键成功因素包括：

1. **完善的向后兼容机制**
2. **详细的迁移工具和文档**
3. **充分的测试和验证**
4. **团队培训和沟通**

建议按照计划分阶段实施，每个阶段完成后进行充分测试，确保系统稳定性。 