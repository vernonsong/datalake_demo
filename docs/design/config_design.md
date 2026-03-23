# 配置模块设计文档

## 1. 概述

配置模块负责管理应用配置，支持：
- YAML配置文件读取
- 占位符替换（从配置中心获取值）
- 多环境配置支持
- 配置文件合并与替换

## 2. 目录结构

```
config/
├── base.yaml           # 基础配置
├── inter.yaml          # inter类别基础配置
├── inter-dev.yaml      # inter类别dev环境配置
├── inter-sit.yaml      # inter类别sit环境配置
├── prod.yaml           # prod类别基础配置
└── prod-prod.yaml     # prod类别prod环境配置
```

## 3. 配置文件命名规范

```
{category}.yaml           # 类别基础配置（无中划线）
{category}-{env}.yaml    # 类别环境配置
```

## 4. 合并与替换规则

### 4.1 规则说明

| 关系 | 条件 | 示例 |
|------|------|------|
| **合并** | 中划线之前不同名，或没有中划线 | base + inter + inter-dev |
| **替换** | 中划线之前相同，之后不同 | inter-sit 替换 inter-dev |

### 4.2 合并顺序（从低到高）

找到所有匹配的文件，按以下顺序合并：
1. 无中划线的文件（base, inter, prod等）
2. 中划线前不匹配当前环境的文件
3. 中划线前匹配当前环境的文件

### 4.3 示例：ENV=dev

假设存在配置文件：
- base.yaml
- inter.yaml
- inter-dev.yaml
- inter-sit.yaml
- prod.yaml
- prod-prod.yaml

匹配`dev`环境的文件：
- `base.yaml` - 无中划线，合并
- `inter.yaml` - 无中划线，合并
- `inter-dev.yaml` - 中划线前`inter`匹配，合并
- `prod.yaml` - 无中划线，合并

最终合并顺序（优先级从低到高）：
1. base.yaml (最低)
2. inter.yaml
3. inter-dev.yaml (最高，替换前面的inter相关配置)
4. prod.yaml

## 5. 占位符

### 5.1 占位符格式

```yaml
# 根级占位符
api_url: ${api_url}

# 嵌套占位符
database:
  host: ${database.host}
  port: ${database.port}
```

### 5.2 占位符来源

占位符从**配置中心服务**获取值进行替换。

### 5.3 替换流程

```
1. 加载YAML配置文件
2. 按规则合并配置文件
3. 解析占位符 ${key}
4. 调用配置中心获取值
5. 替换占位符
6. 返回最终配置
```

## 6. 模块设计

### 6.1 核心类

```python
class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str, env: str):
        """初始化配置管理器

        Args:
            config_dir: 配置目录路径
            env: 环境名称 (dev/sit/prod)
        """

    def load_config(self) -> dict:
        """加载并合并配置"""

    def _get_matching_files(self, env: str) -> list:
        """获取匹配当前环境的配置文件列表"""

    def _load_yaml(self, filename: str) -> dict:
        """加载单个YAML文件"""

    def _merge_configs(self, files: list) -> dict:
        """按规则合并配置文件"""

    def _replace_placeholders(self, config: dict) -> dict:
        """替换占位符"""
```

### 6.2 配置中心集成

```python
class ConfigServiceClient:
    """配置中心客户端"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_value(self, key: str) -> str:
        """获取配置值"""
```

## 7. 使用示例

### 7.1 配置文件

**config/base.yaml**
```yaml
app:
  name: 智能入湖平台
  version: 0.1.0

database:
  host: ${database.host}
  port: ${database.port}
```

**config/inter.yaml**
```yaml
app:
  env: inter

database:
  host: inter-db.internal
```

**config/inter-dev.yaml**
```yaml
app:
  debug: true

database:
  host: inter-dev-db.internal
```

### 7.2 初始化

```python
from app.config import ConfigManager

config_manager = ConfigManager(
    config_dir="./config",
    env="dev"
)
config = config_manager.load_config()
```

### 7.3 最终配置

```python
{
    "app": {
        "name": "智能入湖平台",
        "version": "0.1.0",
        "env": "inter",
        "debug": true
    },
    "database": {
        "host": "inter-dev-db.internal",
        "port": 3306
    }
}
```

## 8. 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| 配置文件不存在 | 跳过，使用已有配置 |
| 占位符未找到 | 抛出异常 |
| 配置中心不可用 | 抛出异常 |

## 9. 优先级总结

配置来源优先级（从低到高）：
1. 无中划线配置文件（base, inter, prod等）
2. 中划线前不匹配环境的文件
3. 中划线前匹配环境的文件（替换前面同类别配置）
4. 配置中心（用于占位符替换）
