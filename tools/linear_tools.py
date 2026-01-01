"""
Linear 工具
用于创建和管理Linear任务
"""

import os
import requests
from crewai.tools import BaseTool
from pydantic import Field, BaseModel
from typing import Type


class CreateIssueInput(BaseModel):
    title: str = Field(description="任务标题")
    description: str = Field(description="任务描述(支持Markdown)")
    labels: str = Field(default="", description="标签，用逗号分隔，如 '前端,高优先级'")


class GetIssueInput(BaseModel):
    issue_id: str = Field(description="任务ID或标识符，如 'Y-123'")


class UpdateIssueStatusInput(BaseModel):
    issue_id: str = Field(description="任务ID")
    status: str = Field(description="新状态，如 'In Progress', 'Done', 'Canceled'")


class ListIssuesInput(BaseModel):
    status: str = Field(default="Todo", description="筛选状态，如 'Todo', 'In Progress', 'Done'")


def get_linear_client():
    api_key = os.getenv("LINEAR_API_KEY")
    team_id = os.getenv("LINEAR_TEAM_ID")
    return api_key, team_id


def graphql_request(query: str, variables: dict = None):
    api_key, _ = get_linear_client()
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    } if api_key else {}
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(
        "https://api.linear.app/graphql",
        json=payload,
        headers=headers
    )
    return response.json()


class CreateIssueTool(BaseTool):
    name: str = "创建Linear任务"
    description: str = "在Linear中创建新任务"
    args_schema: Type[BaseModel] = CreateIssueInput

    def _run(self, title: str, description: str, labels: str = "") -> str:
        api_key, team_id = get_linear_client()
        if not api_key:
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
                "teamId": team_id,
                "title": title,
                "description": description
            }
        }
        
        try:
            result = graphql_request(query, variables)
            
            if "errors" in result:
                return f"错误: {result['errors']}"
            
            issue = result["data"]["issueCreate"]["issue"]
            return f"✅ 任务已创建: [{issue['identifier']}] {issue['title']}\n🔗 {issue['url']}"
            
        except Exception as e:
            return f"错误: {str(e)}"


class GetIssueTool(BaseTool):
    name: str = "获取Linear任务"
    description: str = "获取Linear任务详情"
    args_schema: Type[BaseModel] = GetIssueInput

    def _run(self, issue_id: str) -> str:
        api_key, _ = get_linear_client()
        if not api_key:
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
            result = graphql_request(query, {"id": issue_id})
            
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


class UpdateIssueStatusTool(BaseTool):
    name: str = "更新Linear任务状态"
    description: str = "更新Linear任务状态"
    args_schema: Type[BaseModel] = UpdateIssueStatusInput

    def _run(self, issue_id: str, status: str) -> str:
        api_key, team_id = get_linear_client()
        if not api_key:
            return "错误: Linear未配置"
        
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
            states_result = graphql_request(states_query, {"teamId": team_id})
            states = states_result["data"]["team"]["states"]["nodes"]
            
            state_id = None
            for state in states:
                if state["name"].lower() == status.lower():
                    state_id = state["id"]
                    break
            
            if not state_id:
                available = [s["name"] for s in states]
                return f"错误: 未找到状态 '{status}'，可用状态: {', '.join(available)}"
            
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
            
            result = graphql_request(update_query, {
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


class ListIssuesTool(BaseTool):
    name: str = "列出Linear任务"
    description: str = "列出Linear团队的任务"
    args_schema: Type[BaseModel] = ListIssuesInput

    def _run(self, status: str = "Todo") -> str:
        api_key, team_id = get_linear_client()
        if not api_key:
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
            result = graphql_request(query, {"teamId": team_id})
            issues = result["data"]["team"]["issues"]["nodes"]
            
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


class LinearTools:
    """Linear操作工具集"""
    
    def __init__(self):
        self.create_issue = CreateIssueTool()
        self.get_issue = GetIssueTool()
        self.update_issue_status = UpdateIssueStatusTool()
        self.list_issues = ListIssuesTool()
