#!/usr/bin/env python3
"""
AI 开发团队 - 主入口
让AI团队24小时为你工作

使用方法:
    python main.py "你的需求描述"
    
示例:
    python main.py "给Y平台添加预测市场功能"
"""

import os
import sys
from dotenv import load_dotenv
from crew import YPlatformDevCrew

# 加载环境变量
load_dotenv()

def main():
    # 检查API Key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ 错误: 请在 .env 文件中设置 ANTHROPIC_API_KEY")
        print("   复制 .env.example 为 .env 并填入你的API Key")
        sys.exit(1)
    
    # 获取需求
    if len(sys.argv) > 1:
        requirement = " ".join(sys.argv[1:])
    else:
        print("🤖 AI开发团队已就绪!")
        print("-" * 50)
        requirement = input("请输入你的需求: ").strip()
        
    if not requirement:
        print("❌ 请提供需求描述")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🚀 AI开发团队开始工作")
    print("=" * 50)
    print(f"\n📋 需求: {requirement}\n")
    
    # 启动AI团队
    crew = YPlatformDevCrew()
    result = crew.run(requirement)
    
    print("\n" + "=" * 50)
    print("✅ 任务完成!")
    print("=" * 50)
    print(result)

if __name__ == "__main__":
    main()
