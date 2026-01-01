"""
GitHub 工具
用于读取、创建、更新GitHub仓库中的文件
"""

import os
import base64
from github import Github
from crewai_tools import tool

class GitHubTools:
    """GitHub操作工具集"""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo_name = os.getenv("GITHUB_REPO")  # 格式: owner/repo
        
        if self.token and self.repo_name:
            self.github = Github(self.token)
            self.repo = self.github.get_repo(self.repo_name)
        else:
            self.github = None
            self.repo = None
    
    @tool("列出仓库文件")
    def list_files(self, path: str = "") -> str:
        """
        列出GitHub仓库中指定路径的文件和目录
        
        Args:
            path: 仓库中的路径，如 "src/components" 或留空表示根目录
        
        Returns:
            文件和目录列表
        """
        if not self.repo:
            return "错误: GitHub未配置，请设置GITHUB_TOKEN和GITHUB_REPO"
        
        try:
            contents = self.repo.get_contents(path)
            result = f"📁 {path or '根目录'} 下的内容:\n\n"
            
            dirs = []
            files = []
            
            for content in contents:
                if content.type == "dir":
                    dirs.append(f"📂 {content.name}/")
                else:
                    files.append(f"📄 {content.name}")
            
            result += "\n".join(sorted(dirs) + sorted(files))
            return result
            
        except Exception as e:
            return f"错误: {str(e)}"
    
    @tool("读取文件内容")
    def read_file(self, file_path: str) -> str:
        """
        读取GitHub仓库中的文件内容
        
        Args:
            file_path: 文件路径，如 "src/components/Button.tsx"
        
        Returns:
            文件内容
        """
        if not self.repo:
            return "错误: GitHub未配置，请设置GITHUB_TOKEN和GITHUB_REPO"
        
        try:
            content = self.repo.get_contents(file_path)
            decoded = base64.b64decode(content.content).decode('utf-8')
            return f"📄 {file_path}:\n\n```\n{decoded}\n```"
            
        except Exception as e:
            return f"错误: 无法读取 {file_path}: {str(e)}"
    
    @tool("创建新文件")
    def create_file(self, file_path: str, content: str, commit_message: str) -> str:
        """
        在GitHub仓库中创建新文件
        
        Args:
            file_path: 文件路径，如 "src/components/NewComponent.tsx"
            content: 文件内容
            commit_message: 提交信息
        
        Returns:
            创建结果
        """
        if not self.repo:
            return "错误: GitHub未配置，请设置GITHUB_TOKEN和GITHUB_REPO"
        
        try:
            # 获取或创建开发分支
            branch = os.getenv("GITHUB_BRANCH", "ai-dev")
            
            # 尝试获取分支，如果不存在则创建
            try:
                self.repo.get_branch(branch)
            except:
                # 从main创建新分支
                main = self.repo.get_branch("main")
                self.repo.create_git_ref(f"refs/heads/{branch}", main.commit.sha)
            
            # 创建文件
            self.repo.create_file(
                path=file_path,
                message=commit_message,
                content=content,
                branch=branch
            )
            
            return f"✅ 文件已创建: {file_path} (分支: {branch})"
            
        except Exception as e:
            return f"错误: 无法创建文件: {str(e)}"
    
    @tool("更新文件")
    def update_file(self, file_path: str, new_content: str, commit_message: str) -> str:
        """
        更新GitHub仓库中的文件
        
        Args:
            file_path: 文件路径
            new_content: 新的文件内容
            commit_message: 提交信息
        
        Returns:
            更新结果
        """
        if not self.repo:
            return "错误: GitHub未配置，请设置GITHUB_TOKEN和GITHUB_REPO"
        
        try:
            branch = os.getenv("GITHUB_BRANCH", "ai-dev")
            
            # 获取当前文件
            contents = self.repo.get_contents(file_path, ref=branch)
            
            # 更新文件
            self.repo.update_file(
                path=file_path,
                message=commit_message,
                content=new_content,
                sha=contents.sha,
                branch=branch
            )
            
            return f"✅ 文件已更新: {file_path}"
            
        except Exception as e:
            return f"错误: 无法更新文件: {str(e)}"
    
    @tool("创建Pull Request")
    def create_pr(self, title: str, body: str) -> str:
        """
        创建Pull Request
        
        Args:
            title: PR标题
            body: PR描述
        
        Returns:
            PR链接
        """
        if not self.repo:
            return "错误: GitHub未配置，请设置GITHUB_TOKEN和GITHUB_REPO"
        
        try:
            branch = os.getenv("GITHUB_BRANCH", "ai-dev")
            base = os.getenv("GITHUB_BASE_BRANCH", "main")
            
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=branch,
                base=base
            )
            
            return f"✅ PR已创建: {pr.html_url}"
            
        except Exception as e:
            return f"错误: 无法创建PR: {str(e)}"
