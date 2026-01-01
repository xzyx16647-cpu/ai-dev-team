"""
Linear 工具
用于创建和管理Linear任务
"""

import os
import requests
from crewai_tools import tool

class LinearTools:
    """Linear操作工具集"""
    
    def __init__(self):
        self.api_key = os.getenv("LINEAR_API_KEY")
        self.team_id = os.getenv("LINEAR_TEAM_ID")
        self.api_url = "https://api.linear.app/graphql"
        
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        } if self.api_key else {}
    
    def _graphql_request(self, query: str, variables: dict = None):
        """发送GraphQL请求"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = requests.post(
            self.api_url,
            json=payload,
            headers=self.headers
        )
        return response.json()
    
    @tool("创建Linear任务")
    def create_issue(self, title: str, description: str, labels: str = "") -> str:
        """
        在Linear中创建新任务
        
        Args:
            title: 任务标题
            description: 任务描述(支持Markdown)
            labels: 标签，用逗号分隔，如 "前端,高优先级"
        
        Returns:
            创建结果和任务链接
        """
        if not self.api_key:
            return "错误: Linear未配置，请设置LINEAR_API_KEY"
        
        query = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                }
            }
        }
        """
        
        variables = {
            "input": {
                "teamId": self.team_id,
                "title": title,
                "description": description
            }
        }
        
        try:
            result = self._graphql_request(query, variables)
            
            if "errors" in result:
                return f"错误: {result['errors']}"
            
            issue = result["data"]["issueCreate"]["issue"]
            return f"✅ 任务已创建: [{issue['identifier']}] {issue['title']}\n🔗 {issue['url']}"
            
        except Exception as e:
            return f"错误: {str(e)}"
    
    @tool("获取Linear任务")
    def get_issue(self, issue_id: str) -> str:
        """
        获取Linear任务详情
        
        Args:
            issue_id: 任务ID或标识符，如 "Y-123"
        
        Returns:
            任务详情
        """
        if not self.api_key:
            return "错误: Linear未配置"
        
        query = """
        query GetIssue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                state {
                    name
                }
                assignee {
                    name
                }
                labels {
                    nodes {
                        name
                    }
                }
            }
        }
        """
        
        try:
            result = self._graphql_request(query, {"id": issue_id})
            
            if "errors" in result:
                return f"错误: {result['errors']}"
            
            issue = result["data"]["issue"]
            labels = [l["name"] for l in issue["labels"]["nodes"]]
            
            return f"""
📋 {issue['identifier']}: {issue['title']}
状态: {issue['state']['name']}
标签: {', '.join(labels) if labels else '无'}
描述: {issue['description'] or '无描述'}
"""
            
        except Exception as e:
            return f"错误: {str(e)}"
    
    @tool("更新Linear任务状态")
    def update_issue_status(self, issue_id: str, status: str) -> str:
        """
        更新Linear任务状态
        
        Args:
            issue_id: 任务ID
            status: 新状态，如 "In Progress", "Done", "Canceled"
        
        Returns:
            更新结果
        """
        if not self.api_key:
            return "错误: Linear未配置"
        
        # 首先获取状态ID
        states_query = """
        query GetStates($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """
        
        try:
            states_result = self._graphql_request(states_query, {"teamId": self.team_id})
            states = states_result["data"]["team"]["states"]["nodes"]
            
            state_id = None
            for state in states:
                if state["name"].lower() == status.lower():
                    state_id = state["id"]
                    break
            
            if not state_id:
                available = [s["name"] for s in states]
                return f"错误: 未找到状态 '{status}'，可用状态: {', '.join(available)}"
            
            # 更新状态
            update_query = """
            mutation UpdateIssue($id: String!, $stateId: String!) {
                issueUpdate(id: $id, input: { stateId: $stateId }) {
                    success
                    issue {
                        identifier
                        state {
                            name
                        }
                    }
                }
            }
            """
            
            result = self._graphql_request(update_query, {
                "id": issue_id,
                "stateId": state_id
            })
            
            if result["data"]["issueUpdate"]["success"]:
                issue = result["data"]["issueUpdate"]["issue"]
                return f"✅ {issue['identifier']} 状态已更新为: {issue['state']['name']}"
            else:
                return "错误: 更新失败"
                
        except Exception as e:
            return f"错误: {str(e)}"
    
    @tool("列出Linear任务")
    def list_issues(self, status: str = "Todo") -> str:
        """
        列出Linear团队的任务
        
        Args:
            status: 筛选状态，如 "Todo", "In Progress", "Done"
        
        Returns:
            任务列表
        """
        if not self.api_key:
            return "错误: Linear未配置"
        
        query = """
        query ListIssues($teamId: String!) {
            team(id: $teamId) {
                issues(first: 20, orderBy: updatedAt) {
                    nodes {
                        identifier
                        title
                        state {
                            name
                        }
                        priority
                    }
                }
            }
        }
        """
        
        try:
            result = self._graphql_request(query, {"teamId": self.team_id})
            issues = result["data"]["team"]["issues"]["nodes"]
            
            # 筛选状态
            filtered = [i for i in issues if i["state"]["name"].lower() == status.lower()] if status else issues
            
            if not filtered:
                return f"没有找到状态为 '{status}' 的任务"
            
            output = f"📋 {status} 状态的任务:\n\n"
            for issue in filtered:
                priority_emoji = ["⬜", "🟡", "🟠", "🔴", "⚫"][issue.get("priority", 0)]
                output += f"{priority_emoji} [{issue['identifier']}] {issue['title']}\n"
            
            return output
            
        except Exception as e:
            return f"错误: {str(e)}"
