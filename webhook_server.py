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
from crew import YPlatformDevCrew

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
    """在后台处理任务"""
    print(f"\n🚀 开始处理任务: {issue_data.get('title', 'Unknown')}")
    
    try:
        crew = YPlatformDevCrew()
        
        # 构建需求描述
        requirement = f"""
        任务: {issue_data.get('title', '')}
        
        描述:
        {issue_data.get('description', '无描述')}
        
        标签: {', '.join(issue_data.get('labels', []))}
        """
        
        result = crew.run(requirement)
        print(f"✅ 任务完成: {issue_data.get('title')}")
        print(result)
        
    except Exception as e:
        print(f"❌ 任务失败: {str(e)}")

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
    
    # 验证签名
    signature = request.headers.get("Linear-Signature", "")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    try:
        data = request.json
        
        # 只处理Issue创建和更新事件
        action = data.get("action")
        event_type = data.get("type")
        
        print(f"📨 收到Webhook: {event_type} - {action}")
        
        if event_type == "Issue" and action in ["create", "update"]:
            issue = data.get("data", {})
            
            # 检查是否有特定标签触发AI处理
            labels = [l.get("name", "") for l in issue.get("labels", {}).get("nodes", [])]
            
            # 如果有 "ai-task" 标签，或者任务标题包含 "[AI]"
            should_process = (
                "ai-task" in labels or
                issue.get("title", "").startswith("[AI]")
            )
            
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
