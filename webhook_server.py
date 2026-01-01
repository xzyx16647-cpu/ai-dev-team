#!/usr/bin/env python3
"""
Webhook 服务器
自动监听Linear任务，触发AI团队工作

部署后，将Webhook URL配置到Linear:
Linear Settings -> API -> Webhooks -> Add webhook
"""

import os
import json
import hmac
import hashlib
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from threading import Thread
from workflows.task_router import TaskRouter
from workflows.pm_workflow import PMWorkflow
from workflows.execution_workflow import ExecutionWorkflow

load_dotenv()

app = Flask(__name__)

# Webhook密钥 (可选，用于验证请求来源)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

def verify_signature(payload, signature):
    """验证Linear Webhook签名"""
    if not WEBHOOK_SECRET:
        return True
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)

def process_task(issue_data):
    """在后台处理任务 - 使用新的工作流系统"""
    print(f"\n🚀 开始处理任务: {issue_data.get('title', 'Unknown')}")
    print(f"📋 任务数据: {json.dumps(issue_data, indent=2, ensure_ascii=False)[:500]}...")
    
    try:
        # 路由任务
        router = TaskRouter()
        workflow_type = router.route(issue_data)
        
        print(f"🔀 路由结果: {workflow_type}")
        
        if workflow_type == "pm_mode":
            # PM模式：分析需求，创建子任务
            print("📋 执行PM工作流...")
            pm_workflow = PMWorkflow()
            result = pm_workflow.run(issue_data)
            print(f"✅ PM工作流完成: {result.get('message', '')}")
            
        elif workflow_type in ["frontend", "backend", "database", "review"]:
            # 执行模式：运行单个智能体
            print(f"🤖 执行{workflow_type}工作流...")
            execution_workflow = ExecutionWorkflow()
            result = execution_workflow.run(workflow_type, issue_data)
            print(f"✅ {workflow_type}工作流完成: {result.get('message', '')}")
            
        else:
            print(f"⏭️ 跳过任务: 未匹配到工作流类型")
            print(f"   标题: {issue_data.get('title', '')}")
            print(f"   标签: {issue_data.get('labels', [])}")
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        
        # 检查是否是rate limit错误
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            print(f"⚠️ API限流错误: Anthropic API调用频率超限")
            print(f"💡 建议: 等待1-2分钟后重试，或减少任务复杂度")
            print(f"📊 当前限制: 每分钟30,000 input tokens")
        else:
            print(f"❌ 任务失败: {error_msg}")
        
        print(f"📚 错误详情:\n{traceback.format_exc()}")

@app.route("/", methods=["GET"])
def home():
    """健康检查"""
    return jsonify({
        "status": "running",
        "message": "AI Dev Team Webhook Server"
    })

@app.route("/webhook/linear", methods=["POST"])
def linear_webhook():
    """接收Linear Webhook"""
    
    # 检查是否禁用了webhook
    if os.getenv("DISABLE_WEBHOOK", "").lower() == "true":
        print("⏸️ Webhook处理已禁用 (DISABLE_WEBHOOK=true)")
        return jsonify({
            "status": "disabled",
            "message": "Webhook processing is currently disabled"
        }), 200
    
    # 验证签名
    signature = request.headers.get("Linear-Signature", "")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    try:
        data = request.json
        
        # 调试：打印接收到的数据结构
        print(f"📦 收到Webhook数据: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
        
        # 只处理Issue创建和更新事件
        action = data.get("action")
        event_type = data.get("type")
        
        print(f"📨 收到Webhook: {event_type} - {action}")
        
        if event_type == "Issue" and action in ["create", "update"]:
            issue = data.get("data", {})
            
            # 检查是否有特定标签触发AI处理
            # Linear webhook的labels可能是字典或列表
            labels_raw = issue.get("labels", {})
            labels = []
            
            if isinstance(labels_raw, dict):
                # 如果是字典，尝试获取nodes
                labels = [l.get("name", "") if isinstance(l, dict) else str(l) 
                          for l in labels_raw.get("nodes", [])]
            elif isinstance(labels_raw, list):
                # 如果直接是列表
                labels = [l.get("name", "") if isinstance(l, dict) else str(l) 
                          for l in labels_raw]
            
            print(f"🏷️ 标签: {labels}")
            
            # 如果有 "ai-task" 标签，或者任务标题包含 "[AI]"
            title = issue.get("title", "")
            should_process = (
                "ai-task" in labels or
                title.startswith("[AI]")
            )
            
            print(f"📋 任务标题: {title}")
            print(f"✅ 是否处理: {should_process}")
            
            if should_process:
                # 在后台线程处理，避免超时
                thread = Thread(target=process_task, args=(issue,))
                thread.start()
                
                return jsonify({
                    "status": "accepted",
                    "message": f"Processing: {issue.get('title')}"
                })
            else:
                return jsonify({
                    "status": "skipped",
                    "message": "No ai-task label or [AI] prefix"
                })
        
        return jsonify({"status": "ignored", "message": f"Event type: {event_type}"})
        
    except Exception as e:
        print(f"❌ Webhook错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/webhook/github", methods=["POST"])
def github_webhook():
    """接收GitHub Webhook (用于PR comment触发)"""
    
    # 检查是否禁用了webhook
    if os.getenv("DISABLE_WEBHOOK", "").lower() == "true":
        print("⏸️ Webhook处理已禁用 (DISABLE_WEBHOOK=true)")
        return jsonify({
            "status": "disabled",
            "message": "Webhook processing is currently disabled"
        }), 200
    
    try:
        event = request.headers.get("X-GitHub-Event", "")
        data = request.json
        
        print(f"📨 GitHub Webhook: {event}")
        
        # 处理PR评论
        if event == "issue_comment":
            comment = data.get("comment", {})
            body = comment.get("body", "")
            
            # 如果评论中@了AI
            if "@ai-dev" in body.lower() or "/ai" in body.lower():
                issue = data.get("issue", {})
                
                task = {
                    "title": f"PR反馈: {issue.get('title', '')}",
                    "description": body
                }
                
                thread = Thread(target=process_task, args=(task,))
                thread.start()
                
                return jsonify({"status": "accepted"})
        
        return jsonify({"status": "ignored"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/trigger", methods=["POST"])
def manual_trigger():
    """手动触发任务 (用于测试)"""
    
    # 检查是否禁用了webhook
    if os.getenv("DISABLE_WEBHOOK", "").lower() == "true":
        print("⏸️ Webhook处理已禁用 (DISABLE_WEBHOOK=true)")
        return jsonify({
            "status": "disabled",
            "message": "Webhook processing is currently disabled"
        }), 200
    
    try:
        data = request.json
        requirement = data.get("requirement", "")
        
        if not requirement:
            return jsonify({"error": "Missing requirement"}), 400
        
        task = {"title": requirement, "description": requirement}
        thread = Thread(target=process_task, args=(task,))
        thread.start()
        
        return jsonify({
            "status": "accepted",
            "message": f"Processing: {requirement[:50]}..."
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    
    print("=" * 50)
    print("🤖 AI Dev Team Webhook Server")
    print("=" * 50)
    print(f"🌐 Running on port {port}")
    print(f"📡 Linear Webhook: http://localhost:{port}/webhook/linear")
    print(f"📡 GitHub Webhook: http://localhost:{port}/webhook/github")
    print(f"🔧 Manual trigger: POST http://localhost:{port}/trigger")
    print("=" * 50)
    
    app.run(host="0.0.0.0", port=port)
