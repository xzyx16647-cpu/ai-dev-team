#!/bin/bash
# 检查部署状态

echo "🔍 检查部署状态..."
echo ""

# 检查GitHub最新提交
echo "📦 GitHub最新提交:"
git log --oneline -1
echo ""

# 检查Railway部署URL
echo "🌐 Railway部署URL应该是:"
echo "   https://web-production-6f3c7.up.railway.app"
echo ""

# 测试健康检查
echo "🏥 测试健康检查端点:"
curl -s https://web-production-6f3c7.up.railway.app/ | head -20
echo ""

echo "✅ 如果看到 'status: running'，说明部署成功！"
echo ""
echo "📋 下一步："
echo "   1. 在Linear创建任务: [AI] 测试新工作流"
echo "   2. 查看Railway Deploy Logs确认工作流执行"

