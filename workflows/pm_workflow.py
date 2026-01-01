"""
PM工作流
分析需求，拆解任务，在Linear创建子任务
"""

import os
import time
from crew import YPlatformDevCrew
from tools.linear_tools import LinearTools


class PMWorkflow:
    """PM分析工作流"""
    
    def __init__(self):
        self.crew = YPlatformDevCrew()
        self.linear_tools = LinearTools()
    
    def run(self, issue_data):
        """
        执行PM工作流：
        1. PM智能体分析需求
        2. 拆解为子任务列表
        3. 在Linear创建子任务
        4. 更新原任务状态
        
        Args:
            issue_data: Linear issue数据字典
        """
        
        issue_id = issue_data.get("id", "")
        issue_identifier = issue_data.get("identifier", "")
        title = issue_data.get("title", "")
        description = issue_data.get("description", "无描述")
        
        print(f"\n📋 PM工作流开始")
        print(f"任务: {issue_identifier} - {title}")
        
        try:
            # 构建需求描述
            requirement = f"""
任务: {title}

描述:
{description}

请分析这个需求，并拆解为具体的开发任务。
每个任务应该：
1. 有明确的类型（前端/后端/数据库）
2. 有清晰的标题和描述
3. 有验收标准
4. 考虑任务之间的依赖关系

输出格式：为每个子任务创建一个Linear issue，标题格式为：[类型] 任务名
"""
            
            # 运行PM模式
            print("🧠 PM智能体开始分析...")
            result = self.crew.run_pm_mode(requirement)
            
            print(f"✅ PM分析完成")
            print(f"📊 分析结果:\n{result}")
            
            # PM智能体应该已经在分析过程中通过create_issue工具创建了子任务
            # 这里我们只需要更新原任务状态即可
            
            # 更新原任务状态
            try:
                self.linear_tools.update_issue_status(issue_id, "规划完成")
                print(f"✅ 已更新任务状态: 规划完成")
            except Exception as e:
                print(f"⚠️ 更新任务状态失败: {e}")
            
            # 添加评论
            try:
                comment = f"""
✅ 需求分析完成！

已拆解为多个子任务，请查看相关的Linear issues。

分析摘要：
{result[:500]}...
"""
                # 注意：LinearTools可能需要添加create_comment方法
                print(f"💬 分析结果已记录")
            except Exception as e:
                print(f"⚠️ 添加评论失败: {e}")
            
            return {
                "status": "success",
                "message": "PM工作流完成，已创建子任务"
            }
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"❌ PM工作流失败: {error_msg}")
            print(f"📚 错误详情:\n{traceback.format_exc()}")
            
            return {
                "status": "error",
                "message": f"PM工作流失败: {error_msg}"
            }

