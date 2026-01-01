"""
GitHub 工具
用于读取、创建、更新GitHub仓库中的文件
"""

import os
import base64
from github import Github
from crewai.tools import BaseTool
from pydantic import Field
from typing import Type
from pydantic import BaseModel


class ListFilesInput(BaseModel):
    path: str = Field(default="", description="仓库中的路径，如 'src/components' 或留空表示根目录")


class ReadFileInput(BaseModel):
    file_path: str = Field(description="文件路径，如 'src/components/Button.tsx'")


class CreateFileInput(BaseModel):
    file_path: str = Field(description="文件路径，如 'src/components/NewComponent.tsx'")
    content: str = Field(description="文件内容")
    commit_message: str = Field(description="提交信息")


class UpdateFileInput(BaseModel):
    file_path: str = Field(description="文件路径")
    new_content: str = Field(description="新的文件内容")
    commit_message: str = Field(description="提交信息")


class CreatePRInput(BaseModel):
    title: str = Field(description="PR标题")
    body: str = Field(description="PR描述")


# 全局GitHub客户端
def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO")
    if token and repo_name:
        github = Github(token)
        return github.get_repo(repo_name)
    return None


class ListFilesTool(BaseTool):
    name: str = "列出仓库文件"
    description: str = "列出GitHub仓库中指定路径的文件和目录"
    args_schema: Type[BaseModel] = ListFilesInput

    def _run(self, path: str = "") -> str:
        repo = get_github_client()
        if not repo:
            return "错误: GitHub未配置，请设置GITHUB_TOKEN和GITHUB_REPO"
        
        try:
            contents = repo.get_contents(path)
            
            # get_contents可能返回单个文件或目录列表
            if not isinstance(contents, list):
                contents = [contents]
            
            result = f"📁 {path or '根目录'} 下的内容:\n\n"
            
            dirs = []
            files = []
            
            for content in contents:
                if hasattr(content, 'type'):
                    if content.type == "dir":
                        dirs.append(f"📂 {content.name}/")
                    else:
                        files.append(f"📄 {content.name}")
                else:
                    # 如果content是字符串或其他类型，跳过
                    continue
            
            result += "\n".join(sorted(dirs) + sorted(files))
            return result
            
        except Exception as e:
            return f"错误: {str(e)}"


class ReadFileTool(BaseTool):
    name: str = "读取文件内容"
    description: str = "读取GitHub仓库中的文件内容"
    args_schema: Type[BaseModel] = ReadFileInput

    def _run(self, file_path: str) -> str:
        repo = get_github_client()
        if not repo:
            return "错误: GitHub未配置，请设置GITHUB_TOKEN和GITHUB_REPO"
        
        try:
            content = repo.get_contents(file_path)
            
            # 如果返回的是列表（目录），报错
            if isinstance(content, list):
                return f"错误: {file_path} 是一个目录，不是文件。请使用'列出仓库文件'工具查看目录内容。"
            
            # 确保content有content属性
            if not hasattr(content, 'content'):
                return f"错误: 无法获取 {file_path} 的内容"
            
            decoded = base64.b64decode(content.content).decode('utf-8')
            return f"📄 {file_path}:\n\n```\n{decoded}\n```"
            
        except Exception as e:
            return f"错误: 无法读取 {file_path}: {str(e)}"


class CreateFileTool(BaseTool):
    name: str = "创建新文件"
    description: str = "在GitHub仓库中创建新文件"
    args_schema: Type[BaseModel] = CreateFileInput

    def _run(self, file_path: str, content: str, commit_message: str) -> str:
        repo = get_github_client()
        if not repo:
            return "错误: GitHub未配置，请设置GITHUB_TOKEN和GITHUB_REPO"
        
        try:
            branch = os.getenv("GITHUB_BRANCH", "ai-dev")
            
            try:
                repo.get_branch(branch)
            except:
                main = repo.get_branch("main")
                repo.create_git_ref(f"refs/heads/{branch}", main.commit.sha)
            
            repo.create_file(
                path=file_path,
                message=commit_message,
                content=content,
                branch=branch
            )
            
            return f"✅ 文件已创建: {file_path} (分支: {branch})"
            
        except Exception as e:
            return f"错误: 无法创建文件: {str(e)}"


class UpdateFileTool(BaseTool):
    name: str = "更新文件"
    description: str = "更新GitHub仓库中的文件"
    args_schema: Type[BaseModel] = UpdateFileInput

    def _run(self, file_path: str, new_content: str, commit_message: str) -> str:
        repo = get_github_client()
        if not repo:
            return "错误: GitHub未配置，请设置GITHUB_TOKEN和GITHUB_REPO"
        
        try:
            branch = os.getenv("GITHUB_BRANCH", "ai-dev")
            contents = repo.get_contents(file_path, ref=branch)
            
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=new_content,
                sha=contents.sha,
                branch=branch
            )
            
            return f"✅ 文件已更新: {file_path}"
            
        except Exception as e:
            return f"错误: 无法更新文件: {str(e)}"


class CreatePRTool(BaseTool):
    name: str = "创建Pull Request"
    description: str = "创建Pull Request"
    args_schema: Type[BaseModel] = CreatePRInput

    def _run(self, title: str, body: str) -> str:
        repo = get_github_client()
        if not repo:
            return "错误: GitHub未配置，请设置GITHUB_TOKEN和GITHUB_REPO"
        
        try:
            branch = os.getenv("GITHUB_BRANCH", "ai-dev")
            base = os.getenv("GITHUB_BASE_BRANCH", "main")
            
            pr = repo.create_pull(
                title=title,
                body=body,
                head=branch,
                base=base
            )
            
            return f"✅ PR已创建: {pr.html_url}"
            
        except Exception as e:
            return f"错误: 无法创建PR: {str(e)}"


class GitHubTools:
    """GitHub操作工具集"""
    
    def __init__(self):
        self.list_files = ListFilesTool()
        self.read_file = ReadFileTool()
        self.create_file = CreateFileTool()
        self.update_file = UpdateFileTool()
        self.create_pr = CreatePRTool()
