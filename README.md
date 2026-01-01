# 🤖 AI 开发团队

让AI团队24小时为你的Y平台项目工作。你描述需求，AI团队自动规划、编码、审查、提交。

## 📋 智能体角色

| 角色 | 职责 |
|------|------|
| 🧠 产品经理 | 分析需求，拆解任务，创建Linear Issue |
| 📱 前端工程师 | React + TypeScript，组件开发 |
| ⚙️ 后端工程师 | Python + FastAPI，API开发 |
| 🗄️ 数据库工程师 | Supabase/PostgreSQL，Schema设计 |
| 🔍 代码审查员 | 质量检查，创建PR |

## 🚀 快速开始

### 第一步：安装依赖

```bash
# 进入项目目录
cd ai-dev-team

# 创建虚拟环境 (推荐)
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 第二步：配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑.env文件，填入你的API Key
nano .env  # 或用任何编辑器打开
```

**需要配置的Key:**

1. **ANTHROPIC_API_KEY** (必需)
   - 去 https://console.anthropic.com/ 
   - 创建API Key

2. **GITHUB_TOKEN** (必需)
   - 去 GitHub Settings → Developer settings → Personal access tokens
   - 生成新token，勾选 `repo` 权限

3. **GITHUB_REPO** (必需)
   - 填入你的仓库名，格式: `用户名/仓库名`
   - 例如: `amber/y-platform`

4. **LINEAR_API_KEY** (可选)
   - 去 Linear Settings → API → Personal API keys
   - 生成新key

### 第三步：运行

```bash
# 方式1: 直接传入需求
python main.py "给发帖功能添加图片上传"

# 方式2: 交互式输入
python main.py
# 然后输入你的需求
```

## 📖 使用示例

### 示例1: 添加新功能

```bash
python main.py "给Y平台添加预测市场功能，用户可以创建预测、下注、查看结果"
```

AI团队会:
1. PM分析需求，拆解为具体任务
2. 数据库工程师设计 `prediction_markets` 表
3. 后端工程师创建CRUD API
4. 前端工程师实现UI组件
5. 审查员检查代码，创建PR

### 示例2: 修复Bug

```bash
python main.py "修复发帖时图片上传失败的问题，位置在 src/components/PostEditor.tsx"
```

### 示例3: 优化性能

```bash
python main.py "优化首页加载速度，减少API请求次数"
```

## 🔧 配置说明

### 修改项目结构

如果你的项目结构不同，编辑 `crew.py` 中的 `project_context`:

```python
self.project_context = """
你的项目结构说明...
"""
```

### 添加自定义工具

在 `tools/` 目录下创建新工具:

```python
# tools/my_tool.py
from crewai_tools import tool

@tool("我的工具")
def my_custom_tool(param: str) -> str:
    """工具描述"""
    # 实现
    return "结果"
```

## 🌐 24小时自动运行 (Railway部署)

### 🚂 一键部署到Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

**详细步骤:**

#### 第一步：连接GitHub
1. 访问 [Railway](https://railway.app/) 并注册/登录
2. 点击 **New Project** → **Deploy from GitHub repo**
3. 授权Railway访问你的GitHub
4. 选择 `ai-dev-team` 仓库

#### 第二步：配置环境变量
在Railway项目设置中添加以下环境变量:

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `ANTHROPIC_API_KEY` | ✅ | Claude API密钥 |
| `GITHUB_TOKEN` | ✅ | GitHub Personal Access Token |
| `GITHUB_REPO` | ✅ | 目标仓库 (如: `user/repo`) |
| `LINEAR_API_KEY` | ❌ | Linear API密钥 (如需Linear集成) |
| `LINEAR_TEAM_ID` | ❌ | Linear团队ID |
| `WEBHOOK_SECRET` | ❌ | Webhook验证密钥 |

#### 第三步：获取Webhook URL
1. 部署成功后，Railway会自动分配一个域名
2. 你的Webhook URL格式: `https://your-app.railway.app/webhook/linear`

#### 第四步：配置Linear Webhook (可选)
1. 打开 Linear Settings → API → Webhooks
2. 添加新Webhook，URL填入上面获取的地址
3. 选择触发事件: Issue created, Issue updated
4. 保存

#### 第五步：测试
```bash
# 发送测试请求
curl -X POST https://your-app.railway.app/trigger \
  -H "Content-Type: application/json" \
  -d '{"requirement": "添加一个测试功能"}'
```

### 🔧 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env
# 编辑.env填入你的API密钥

# 启动服务器
python webhook_server.py
```

### 📡 API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/webhook/linear` | POST | Linear Webhook接收 |
| `/webhook/github` | POST | GitHub Webhook接收 |
| `/trigger` | POST | 手动触发任务 |

### 方式2: 自己的服务器 (Docker)

```bash
# 使用Docker部署
docker build -t ai-dev-team .
docker run -d --env-file .env -p 5000:5000 ai-dev-team
```

### 方式3: 自己的服务器 (Supervisor)

```bash
# 安装supervisor
sudo apt install supervisor

# 创建配置
sudo nano /etc/supervisor/conf.d/ai-dev-team.conf
```

```ini
[program:ai-dev-team]
command=/path/to/venv/bin/python /path/to/ai-dev-team/webhook_server.py
autostart=true
autorestart=true
user=your-user
```

## 📁 项目结构

```
ai-dev-team/
├── main.py              # 入口文件
├── crew.py              # 团队协调核心
├── tools/
│   ├── github_tools.py  # GitHub操作
│   ├── linear_tools.py  # Linear操作
│   └── code_tools.py    # 代码分析
├── .env.example         # 环境变量模板
├── requirements.txt     # Python依赖
└── README.md           # 这个文件
```

## ❓ 常见问题

### Q: 为什么AI写的代码不对？

A: AI可能不了解你项目的某些细节，你可以:
- 在需求描述中写清楚文件路径
- 更新 `crew.py` 中的项目上下文
- 让AI先读取相关文件再修改

### Q: 如何查看执行过程？

A: 运行时会输出详细日志，包括每个智能体的思考过程。

### Q: 消耗多少API费用？

A: 大约每次请求 $0.1 - $0.5，取决于代码复杂度。

## 🆘 需要帮助？

- 查看日志输出
- 检查API Key是否正确
- 确认GitHub仓库权限
