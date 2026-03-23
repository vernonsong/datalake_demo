# AGENTS.md

⚠️ **P0 - 最高优先级规则** ⚠️

本文件是项目开发的**指导方针和地图**，拥有最高优先级，必须时刻在你的上下文中，**必须严格遵循**。

---

## Project Overview

智能入湖平台 - 基于Agent Skills的数据入湖自动化平台

## Where to Start

1. 阅读需求文档: `docs/需求文档.md`
2. 阅读Harness规范: `docs/harness规范.md`
3. 阅读Agent Skills技术文档: `docs/AgentSkills技术文档.md`

## Repository Map

```
app/                    # FastAPI应用
├── main.py            # 应用入口
├── config.py          # 配置模块
├── settings.py        # 应用设置
├── core/              # 核心模块
│   ├── clients/       # 上游客户端
│   └── dependencies.py # 依赖注入
├── routers/           # API路由
└── schemas/           # Pydantic数据模型

frontend/              # React 前端应用
├── src/               # 源代码
├── public/            # 公共资源
├── package.json       # 依赖配置
└── vite.config.js     # Vite 配置

mock_service/          # Mock服务(上游系统模拟)
├── api_server.py     # API入口
├── config_service.py # 配置中心
├── token_service.py  # Token服务
└── ...

tests/                 # 测试
├── unit/            # 单元测试
└── integration/     # 集成测试

docs/                  # 文档
├── api/              # API文档
├── design/           # 设计文档
├── tasks/            # 任务记录
├── 需求文档.md
├── harness规范.md
└── AgentSkills技术文档.md

config/                # YAML配置文件
.env                   # 环境配置
```

## Build, Test, Lint, Run Commands

```bash
# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend && npm install && cd ..

# 启动Mock服务
python -m mock_service.api_server

# 启动FastAPI服务
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动前端服务
cd frontend && npm run dev

# 运行测试
pytest tests/
```

## Architecture

- **FastAPI**: 后端API框架
- **Agent Skills**: 智能体能力框架(参考`docs/AgentSkills技术文档.md`)
- **Harness工程**: 智能体驱动开发规范(参考`docs/harness规范.md`)
- **Mock Service**: 模拟上游系统接口
- **Config模块**: YAML配置管理(参考`docs/design/config_design.md`)

## Key Docs

- [需求文档](docs/需求文档.md)
- [Harness规范](docs/harness规范.md)
- [Agent Skills技术文档](docs/AgentSkills技术文档.md)
- [API文档](docs/api/README.md)
- [配置模块设计](docs/design/config_design.md)
- [配置规范](docs/design/config_spec.md)

## Change Rules

1. 遵循Harness规范 - 人类掌舵，智能体执行
2. 使用渐进式披露 - 给地图不给说明书
3. 维护AGENTS.md - 路径变更时更新
4. 设计文档放docs/design/目录
5. API文档放docs/api/目录
6. **代码中禁止任何默认配置（包括默认值参数），所有配置必须从配置文件或环境变量获取**
7. 客户端必须通过依赖注入获取base_url和token_provider
8. **【强制】每次任务必须在docs/tasks/中记录，格式: yyyy-mm-dd-hh-mm-任务名.md**
9. **【强制】任务完成后必须委托task-completion-validator进行独立验证，验证不通过需继续修改直至通过**

## Task Workflow

```
1. 接收任务 → 2. 创建任务文档 docs/tasks/yyyy-mm-dd-hh-mm-任务名.md
3. 执行任务 → 4. 运行task-completion-validator验证
5. 验证通过 → 完成任务
6. 验证失败 → 返回步骤3继续修改
```

## Validation Checklist

- [ ] 新功能需添加对应测试
- [ ] 配置文件修改需同步更新文档
- [ ] API变更需更新`docs/api/README.md`
- [ ] 设计文档放`docs/design/`目录
- [ ] Settings必须无默认值，所有配置从.env加载
- [ ] 任务完成后运行验证确保通过
