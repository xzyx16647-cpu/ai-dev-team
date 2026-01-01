"""
代码分析工具
用于分析和验证代码质量
"""

import re
from crewai.tools import BaseTool
from pydantic import Field, BaseModel
from typing import Type


class AnalyzeCodeInput(BaseModel):
    code: str = Field(description="要分析的代码")
    language: str = Field(default="typescript", description="编程语言 (typescript/python)")


class GenerateTemplateInput(BaseModel):
    component_type: str = Field(description="模板类型 (react-component/react-hook/fastapi-router/supabase-migration)")
    name: str = Field(description="名称")


class AnalyzeCodeTool(BaseTool):
    name: str = "分析代码"
    description: str = "分析代码质量和潜在问题"
    args_schema: Type[BaseModel] = AnalyzeCodeInput

    def _run(self, code: str, language: str = "typescript") -> str:
        issues = []
        suggestions = []
        
        if language.lower() in ["typescript", "tsx", "javascript", "jsx"]:
            issues, suggestions = self._analyze_typescript(code)
        elif language.lower() == "python":
            issues, suggestions = self._analyze_python(code)
        
        report = "📊 代码分析报告\n" + "=" * 40 + "\n\n"
        
        if issues:
            report += "⚠️ 发现的问题:\n"
            for i, issue in enumerate(issues, 1):
                report += f"  {i}. {issue}\n"
            report += "\n"
        else:
            report += "✅ 未发现明显问题\n\n"
        
        if suggestions:
            report += "💡 改进建议:\n"
            for i, suggestion in enumerate(suggestions, 1):
                report += f"  {i}. {suggestion}\n"
        
        return report
    
    def _analyze_typescript(self, code: str):
        issues = []
        suggestions = []
        
        if "console.log" in code:
            issues.append("包含console.log调试语句，生产环境应移除")
        
        if re.search(r':\s*any\b', code):
            issues.append("使用了any类型，建议使用具体类型")
        
        if re.search(r'catch\s*\([^)]*\)\s*{\s*}', code):
            issues.append("存在空的catch块，应处理错误")
        
        if re.search(r'http://|https://', code) and 'process.env' not in code:
            suggestions.append("URL可能是硬编码的，建议使用环境变量")
        
        if "useState" in code:
            if not re.search(r'useState<', code):
                suggestions.append("useState建议添加泛型类型")
        
        if "function" in code or "const" in code:
            if re.search(r'(function|const)\s+[a-z]', code):
                if "export" in code:
                    suggestions.append("React组件名应使用PascalCase")
        
        if "useEffect" in code:
            if re.search(r'useEffect\([^)]+,\s*\[\s*\]\)', code):
                suggestions.append("useEffect依赖数组为空，确认是否需要添加依赖")
        
        return issues, suggestions
    
    def _analyze_python(self, code: str):
        issues = []
        suggestions = []
        
        if re.search(r'\bprint\(', code):
            suggestions.append("包含print语句，生产环境建议使用logging")
        
        if re.search(r'except\s*:', code):
            issues.append("使用了bare except，应指定具体异常类型")
        
        if "TODO" in code or "FIXME" in code:
            suggestions.append("代码中有TODO/FIXME注释，记得处理")
        
        if "def " in code:
            if not re.search(r'def\s+\w+\([^)]*\)\s*->', code):
                suggestions.append("函数缺少返回类型注解")
        
        if re.search(r'[=<>]\s*\d{2,}', code):
            suggestions.append("可能存在魔法数字，建议使用常量")
        
        if "FastAPI" in code or "@app" in code or "@router" in code:
            if "async def" not in code:
                suggestions.append("FastAPI路由建议使用async def")
        
        return issues, suggestions


class GenerateTemplateTool(BaseTool):
    name: str = "生成代码模板"
    description: str = "生成代码模板"
    args_schema: Type[BaseModel] = GenerateTemplateInput

    def _run(self, component_type: str, name: str) -> str:
        templates = {
            "react-component": self._react_component_template,
            "react-hook": self._react_hook_template,
            "fastapi-router": self._fastapi_router_template,
            "supabase-migration": self._supabase_migration_template,
        }
        
        if component_type not in templates:
            return f"未知模板类型: {component_type}\n可用类型: {', '.join(templates.keys())}"
        
        return templates[component_type](name)
    
    def _react_component_template(self, name: str) -> str:
        return f'''import {{ FC }} from 'react';

interface {name}Props {{
  // 定义props
}}

export const {name}: FC<{name}Props> = ({{ }}) => {{
  return (
    <div className="">
      {name}
    </div>
  );
}};

export default {name};
'''
    
    def _react_hook_template(self, name: str) -> str:
        return f'''import {{ useState, useEffect }} from 'react';

interface Use{name}Options {{
  // 定义options
}}

interface Use{name}Return {{
  // 定义返回值
  isLoading: boolean;
  error: Error | null;
}}

export function use{name}(options?: Use{name}Options): Use{name}Return {{
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {{
    // 初始化逻辑
  }}, []);

  return {{
    isLoading,
    error,
  }};
}}
'''
    
    def _fastapi_router_template(self, name: str) -> str:
        name_lower = name.lower()
        return f'''from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/{name_lower}s", tags=["{name}"])


class {name}Create(BaseModel):
    """创建{name}的请求体"""
    pass


class {name}Response(BaseModel):
    """返回的{name}数据"""
    id: str
    created_at: datetime
    updated_at: datetime


@router.get("/", response_model=List[{name}Response])
async def list_{name_lower}s():
    """获取{name}列表"""
    pass


@router.get("/{{id}}", response_model={name}Response)
async def get_{name_lower}(id: str):
    """获取单个{name}"""
    pass


@router.post("/", response_model={name}Response)
async def create_{name_lower}(data: {name}Create):
    """创建{name}"""
    pass


@router.put("/{{id}}", response_model={name}Response)
async def update_{name_lower}(id: str, data: {name}Create):
    """更新{name}"""
    pass


@router.delete("/{{id}}")
async def delete_{name_lower}(id: str):
    """删除{name}"""
    pass
'''
    
    def _supabase_migration_template(self, name: str) -> str:
        table_name = name.lower() + "s"
        return f'''-- Migration: Create {table_name} table
-- Created at: {{timestamp}}

-- Create the table
CREATE TABLE IF NOT EXISTS {table_name} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Add your columns here
    
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_{table_name}_updated_at
    BEFORE UPDATE ON {table_name}
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security
ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;

-- Policies (adjust as needed)
CREATE POLICY "{table_name}_select_policy" ON {table_name}
    FOR SELECT USING (true);

CREATE POLICY "{table_name}_insert_policy" ON {table_name}
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "{table_name}_update_policy" ON {table_name}
    FOR UPDATE USING (auth.uid() IS NOT NULL);

-- Indexes
CREATE INDEX IF NOT EXISTS {table_name}_created_at_idx ON {table_name}(created_at DESC);
'''


class CodeTools:
    """代码分析工具集"""
    
    def __init__(self):
        self.analyze_code = AnalyzeCodeTool()
        self.generate_template = GenerateTemplateTool()
