# 配置管理规范

## 1. 原则

所有配置必须通过配置文件（.env）管理，禁止在代码中硬编码默认值。

## 2. Settings定义规范

### 2.1 必填字段

所有Settings字段必须在`.env`文件中定义，无默认值：

```python
# ❌ 错误：带有默认值
class Settings(BaseSettings):
    app_name: str = "智能入湖平台"  # 禁止

# ✅ 正确：无默认值
class Settings(BaseSettings):
    APP_NAME: str  # 必填
```

### 2.2 命名规范

- 环境变量使用大写字母加下划线：`APP_NAME`
- Python属性使用小驼峰：`app_name`
- 通过`@property`暴露给外部使用

```python
class Settings(BaseSettings):
    APP_NAME: str
    MOCK_SERVICE_URL: str

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def mock_service_url(self) -> str:
        return self.MOCK_SERVICE_URL
```

### 2.3 可选字段

可选字段可以设置默认值，但必须是有意义的默认值：

```python
ALI_API_KEY: Optional[str] = None
```

## 3. .env文件规范

### 3.1 必填配置

所有必填字段必须在.env中定义：

```env
# 应用配置
APP_NAME=智能入湖平台
APP_VERSION=0.1.0
DEBUG=true

# 服务配置
HOST=0.0.0.0
PORT=8000

# 外部服务配置
MOCK_SERVICE_URL=http://localhost:5001
MOCK_API_SECRET=your-secret-key

# JWT配置
JWT_SECRET=your-jwt-secret
```

### 3.2 分组注释

使用分组注释提高可读性：

```env
# ===================
# 应用配置
# ===================
APP_NAME=xxx

# ===================
# 服务配置
# ===================
HOST=xxx
```

## 4. 配置加载流程

```
.env文件 → Settings类 → 代码使用
    ↓
  必须定义
    ↓
  通过@property暴露
```

## 5. 禁止事项

1. ❌ 禁止在Settings中硬编码默认值（可选字段除外）
2. ❌ 禁止在代码中使用硬编码配置
3. ❌ 禁止使用未在.env中定义的配置

## 6. 正确示例

```python
# app/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    HOST: str
    PORT: int
    MOCK_SERVICE_URL: str
    MOCK_API_SECRET: str
    JWT_SECRET: str
    ALI_API_KEY: Optional[str] = None

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    # ... 其他属性

settings = Settings()
```

```env
# .env
APP_NAME=智能入湖平台
APP_VERSION=0.1.0
DEBUG=true
HOST=0.0.0.0
PORT=8000
MOCK_SERVICE_URL=http://localhost:5001
MOCK_API_SECRET=secret
JWT_SECRET=secret
```
