"""
任务路由模块
根据Linear任务的特征，决定执行哪个工作流
"""

class TaskRouter:
    """任务路由器"""
    
    def route(self, issue_data):
        """
        根据Linear任务的特征，决定执行哪个工作流
        
        Args:
            issue_data: Linear issue数据字典
            
        Returns:
            "pm_mode" | "frontend" | "backend" | "database" | "review" | None
        """
        
        # 获取任务信息
        title = issue_data.get("title", "").lower()
        labels_raw = issue_data.get("labels", {})
        state = issue_data.get("state", {}).get("name", "")
        
        # 解析标签
        labels = []
        if isinstance(labels_raw, dict):
            labels = [l.get("name", "").lower() if isinstance(l, dict) else str(l).lower() 
                     for l in labels_raw.get("nodes", [])]
        elif isinstance(labels_raw, list):
            labels = [l.get("name", "").lower() if isinstance(l, dict) else str(l).lower() 
                     for l in labels_raw]
        
        # 规则1: 检查是否是AI生成的子任务（应该执行，不是分析）
        if "ai-generated" in labels:
            return self._get_execution_type(title, labels)
        
        # 规则2: 如果已经规划完成，跳过
        if state.lower() in ["规划完成", "planned", "done"]:
            return None
        
        # 规则3: 标题以 [AI] 开头 → PM模式
        if title.startswith("[ai]"):
            return "pm_mode"
        
        # 规则4: 有 ai-plan 标签 → PM模式
        if "ai-plan" in labels or "ai-planning" in labels:
            return "pm_mode"
        
        # 规则5: 检查是否是执行类型的任务
        execution_type = self._get_execution_type(title, labels)
        if execution_type:
            return execution_type
        
        # 默认：跳过
        return None
    
    def _get_execution_type(self, title, labels):
        """
        根据标题和标签判断执行类型
        
        Returns:
            "frontend" | "backend" | "database" | "review" | None
        """
        
        # 前端任务
        if ("[前端]" in title or "[frontend]" in title or 
            "frontend" in labels or "前端" in labels):
            return "frontend"
        
        # 后端任务
        if ("[后端]" in title or "[backend]" in title or 
            "backend" in labels or "后端" in labels):
            return "backend"
        
        # 数据库任务
        if ("[数据库]" in title or "[database]" in title or 
            "database" in labels or "数据库" in labels or "db" in labels):
            return "database"
        
        # 审查任务
        if ("[审查]" in title or "[review]" in title or 
            "review" in labels or "审查" in labels):
            return "review"
        
        return None

