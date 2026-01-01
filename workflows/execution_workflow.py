"""
执行工作流
根据任务类型，运行对应的单个智能体
"""

import os
from crew import YPlatformDevCrew
from tools.linear_tools import LinearTools


class ExecutionWorkflow:
    """单智能体执行工作流"""
    
    def __init__(self):
        self.crew = YPlatformDevCrew()
        self.linear_tools = LinearTools()
    
    def run(self, task_type, issue_data):
        """
        执行单个智能体的任务
        
        Args:
            task_type: 任务类型 ("frontend" | "backend" | "database" | "review")
            issue_data: Linear issue数据字典
        """
        
        issue_id = issue_data.get("id", "")
        issue_identifier = issue_data.get("identifier", "")
        title = issue_data.get("title", "")
        description = issue_data.get("description", "无描述")
        
        print(f"\n🚀 执行工作流开始")
        print(f"类型: {task_type}")
        print(f"任务: {issue_identifier} - {title}")
        
        try:
            # 构建任务描述
            task_description = f"""
任务: {title}

描述:
{description}

请完成此任务：
1. 分析需求，理解要做什么
2. 查看相关代码文件（如果需要）
3. 创建或更新代码文件
4. 确保代码质量
5. 创建Pull Request
6. 完成后更新Linear任务状态为Done

注意：
- 如果涉及前端，使用React + TypeScript + Tailwind CSS
- 如果涉及后端，使用Python + FastAPI
- 如果涉及数据库，创建Supabase迁移文件
- 代码要符合项目规范
"""
            
            # 运行对应的智能体
            print(f"🤖 运行{task_type}智能体...")
            result = self.crew.run_single_agent(task_type, task_description)
            
            print(f"✅ 任务执行完成")
            print(f"📊 执行结果:\n{result}")
            
            # 更新Linear任务状态为Done
            try:
                self.linear_tools.update_issue_status(issue_id, "Done")
                print(f"✅ 已更新任务状态: Done")
            except Exception as e:
                print(f"⚠️ 更新任务状态失败: {e}")
                # 尝试其他可能的状态名
                try:
                    self.linear_tools.update_issue_status(issue_id, "已完成")
                except:
                    pass
            
            return {
                "status": "success",
                "message": f"{task_type}任务执行完成",
                "result": result
            }
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"❌ 执行工作流失败: {error_msg}")
            print(f"📚 错误详情:\n{traceback.format_exc()}")
            
            # 检查是否是rate limit错误
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                print(f"⚠️ API限流错误，任务稍后会自动重试")
            
            return {
                "status": "error",
                "message": f"执行失败: {error_msg}"
            }

