"""
AI 开发团队 - 团队协调
定义智能体角色和工作流程
"""

import os
from crewai import Agent, Task, Crew, Process
from langchain_anthropic import ChatAnthropic
from tools.github_tools import GitHubTools
from tools.linear_tools import LinearTools
from tools.code_tools import CodeTools

class YPlatformDevCrew:
    """Y平台AI开发团队"""
    
    def __init__(self):
        # 初始化Claude模型
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=4096
        )
        
        # 初始化工具
        self.github_tools = GitHubTools()
        self.linear_tools = LinearTools()
        self.code_tools = CodeTools()
        
        # 项目知识
        self.project_context = """
        Y平台技术栈:
        
        【前端】src/ 目录
        - React 18 + TypeScript
        - Vite 构建
        - Tailwind CSS 样式
        - Zustand 状态管理 (src/stores/)
        - React Router v7 路由 (src/routes/)
        - 组件目录: src/components/
        - 页面目录: src/pages/
        - Hooks目录: src/hooks/
        - API调用: src/api/
        
        【后端】server/ 目录
        - Python + FastAPI
        - 路由: server/routers/
        - 模型: server/models/
        - 服务: server/services/
        - Pydantic数据验证
        
        【数据库】
        - Supabase (PostgreSQL)
        - 迁移文件: supabase/migrations/
        - 表结构定义在migrations中
        
        【部署】
        - 前端: Firebase Hosting
        - 后端: Google Cloud Run
        - Push到GitHub自动部署到dev环境
        """
    
    def _create_agents(self):
        """创建智能体团队"""
        
        # 产品经理智能体
        self.pm_agent = Agent(
            role="产品经理",
            goal="将用户需求分析并拆解为具体可执行的开发任务",
            backstory="""你是一位资深产品经理，同时具备技术背景。
            你擅长理解用户需求，并将其转化为清晰的技术任务。
            你了解Y平台的架构，能够判断需求涉及前端、后端还是数据库。
            你会为每个任务定义清晰的验收标准。""",
            llm=self.llm,
            tools=[self.linear_tools.create_issue, self.github_tools.list_files],
            verbose=True
        )
        
        # 前端智能体
        self.frontend_agent = Agent(
            role="高级前端工程师",
            goal="实现高质量的React组件和用户界面",
            backstory=f"""你是一位React和TypeScript专家，专注于Y平台前端开发。
            
            你的技术栈:
            - React 18 + TypeScript
            - Tailwind CSS (不用写CSS文件，直接用class)
            - Zustand状态管理
            - React Router v7
            - Lucide React图标
            
            代码规范:
            - 使用函数组件和Hooks
            - 类型定义完整
            - 组件职责单一
            - 使用Tailwind的class而不是内联样式
            
            {self.project_context}""",
            llm=self.llm,
            tools=[
                self.github_tools.read_file,
                self.github_tools.create_file,
                self.github_tools.update_file,
                self.code_tools.analyze_code
            ],
            verbose=True
        )
        
        # 后端智能体
        self.backend_agent = Agent(
            role="高级后端工程师",
            goal="实现健壮的API接口和业务逻辑",
            backstory=f"""你是一位Python和FastAPI专家，专注于Y平台后端开发。
            
            你的技术栈:
            - Python 3.11+
            - FastAPI框架
            - Pydantic数据验证
            - SQLAlchemy/Supabase客户端
            - 异步编程 (async/await)
            
            代码规范:
            - RESTful API设计
            - 完整的类型注解
            - 清晰的错误处理
            - 适当的日志记录
            
            {self.project_context}""",
            llm=self.llm,
            tools=[
                self.github_tools.read_file,
                self.github_tools.create_file,
                self.github_tools.update_file,
                self.code_tools.analyze_code
            ],
            verbose=True
        )
        
        # 数据库智能体
        self.database_agent = Agent(
            role="数据库架构师",
            goal="设计高效的数据结构和数据库操作",
            backstory=f"""你是一位数据库专家，专注于Y平台的Supabase/PostgreSQL。
            
            你的职责:
            - 设计表结构
            - 编写迁移文件
            - 优化查询性能
            - 设计索引策略
            - RLS (Row Level Security) 策略
            
            规范:
            - 使用UUID作为主键
            - 表名使用snake_case复数形式
            - 字段命名清晰
            - 适当的外键约束
            - created_at/updated_at时间戳
            
            {self.project_context}""",
            llm=self.llm,
            tools=[
                self.github_tools.read_file,
                self.github_tools.create_file,
                self.code_tools.analyze_code
            ],
            verbose=True
        )
        
        # Code Review智能体
        self.reviewer_agent = Agent(
            role="代码审查员",
            goal="确保代码质量和一致性",
            backstory="""你是一位严格但友善的代码审查员。
            你检查代码的:
            - 正确性和完整性
            - 代码风格一致性
            - 潜在的bug和安全问题
            - 性能问题
            - 前后端接口一致性
            
            你会给出具体的改进建议。""",
            llm=self.llm,
            tools=[
                self.github_tools.read_file,
                self.github_tools.create_pr,
                self.code_tools.analyze_code
            ],
            verbose=True
        )
    
    def _create_tasks(self, requirement: str):
        """根据需求创建任务"""
        
        # 任务1: PM分析需求
        analyze_task = Task(
            description=f"""
            分析以下需求，并制定开发计划:
            
            需求: {requirement}
            
            你需要:
            1. 理解需求的核心目标
            2. 判断涉及哪些部分(前端/后端/数据库)
            3. 拆解为具体的子任务
            4. 确定任务依赖关系和优先级
            5. 为每个任务定义验收标准
            
            输出格式:
            - 需求分析摘要
            - 任务列表(带标签: [前端]/[后端]/[数据库])
            - 任务依赖关系
            - 建议的执行顺序
            """,
            expected_output="详细的开发计划，包含具体任务列表",
            agent=self.pm_agent
        )
        
        # 任务2: 数据库设计(如果需要)
        database_task = Task(
            description="""
            根据PM的开发计划，如果需要数据库改动:
            
            1. 查看现有的数据库结构
            2. 设计新的表结构或修改
            3. 编写Supabase迁移文件
            4. 考虑索引和性能
            
            如果不需要数据库改动，说明原因并跳过。
            """,
            expected_output="数据库迁移文件或说明不需要改动",
            agent=self.database_agent,
            context=[analyze_task]
        )
        
        # 任务3: 后端开发
        backend_task = Task(
            description="""
            根据PM的开发计划和数据库设计:
            
            1. 查看现有的后端代码结构
            2. 实现需要的API接口
            3. 编写业务逻辑
            4. 添加适当的错误处理
            
            确保API设计符合RESTful规范。
            """,
            expected_output="完整的后端代码实现",
            agent=self.backend_agent,
            context=[analyze_task, database_task]
        )
        
        # 任务4: 前端开发
        frontend_task = Task(
            description="""
            根据PM的开发计划和后端API:
            
            1. 查看现有的前端代码结构
            2. 创建需要的React组件
            3. 实现用户界面和交互
            4. 连接后端API
            5. 处理加载和错误状态
            
            使用Tailwind CSS进行样式设计。
            """,
            expected_output="完整的前端代码实现",
            agent=self.frontend_agent,
            context=[analyze_task, backend_task]
        )
        
        # 任务5: 代码审查
        review_task = Task(
            description="""
            审查所有生成的代码:
            
            1. 检查代码质量和规范
            2. 验证前后端接口一致性
            3. 检查潜在问题
            4. 创建Pull Request
            5. 生成代码审查报告
            """,
            expected_output="代码审查报告和PR链接",
            agent=self.reviewer_agent,
            context=[database_task, backend_task, frontend_task]
        )
        
        return [analyze_task, database_task, backend_task, frontend_task, review_task]
    
    def run(self, requirement: str):
        """运行AI开发团队"""
        
        print("🔧 初始化智能体团队...")
        self._create_agents()
        
        print("📝 创建任务...")
        tasks = self._create_tasks(requirement)
        
        print("👥 组建团队...")
        crew = Crew(
            agents=[
                self.pm_agent,
                self.database_agent,
                self.backend_agent,
                self.frontend_agent,
                self.reviewer_agent
            ],
            tasks=tasks,
            process=Process.sequential,  # 按顺序执行
            verbose=True
        )
        
        print("🏃 开始执行...\n")
        result = crew.kickoff()
        
        return result
