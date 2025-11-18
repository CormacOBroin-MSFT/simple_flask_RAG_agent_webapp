# AI Chatbot Integration Guide

## 🚀 Quick Setup

### 1. Prerequisites
- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)
- Azure CLI (for authentication)

### 2. Clone and Install
```bash
git clone <your-repo-url>
cd localChatBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables
Set the following environment variables (in your shell, `.env`, or `.bashrc`):
- `AZURE_AI_ENDPOINT` (e.g. `https://your-endpoint.services.ai.azure.com`)
- `AZURE_AI_PROJECT_NAME` (e.g. `your-project`)
- `AZURE_AI_API_VERSION` (e.g. `2025-05-01`)
- `AZURE_AI_AGENT_ID` (your assistant ID)
- `USE_AZURE_AGENT` (set to `true` to enable agent)
- `BOT_NAME` (optional, UI display name)
- `GREETING_MESSAGE` (optional, UI greeting)
- `FLASK_SECRET_KEY` (recommended, for session security)

Example for bash:
```bash
export AZURE_AI_ENDPOINT="https://your-endpoint.services.ai.azure.com"
export AZURE_AI_PROJECT_NAME="your-project"
export AZURE_AI_API_VERSION="2025-05-01"
export AZURE_AI_AGENT_ID="asst_your_custom_id"
export USE_AZURE_AGENT=true
export FLASK_SECRET_KEY="your-very-secret-key"
```

### 4. Add Your Logo
- Place your logo image as `logo.png` in the folder: `static/images/logo.png`
- The UI will automatically use this file. Recommended size: 48x48px to 128x128px (PNG, transparent background preferred).

### 5. Run the App
```bash
python app.py
```
- Visit [http://localhost:5000](http://localhost:5000) in your browser.

---

## Overview

Azure AI Foundry provides **OpenAI-compatible REST APIs** for interacting with AI agents (assistants). This guide documents the correct patterns, authentication methods, and API calls based on real-world testing for building a custom AI chatbot.

## 🔑 Authentication

### Required Scope
- **Scope**: `https://ai.azure.com/.default`
- **Method**: Bearer token authentication
- **Credential Types**: AzureCliCredential, DefaultAzureCredential

### Get Access Token

```bash
# Using Azure CLI
az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv

# Using Python
from azure.identity import AzureCliCredential

credential = AzureCliCredential()
token = credential.get_token("https://ai.azure.com/.default")
access_token = token.token
```

## 🌐 API Endpoints

Azure AI Foundry has **two different API patterns** that show different agents:

### Base Configuration
```
Base URL: https://your-project.services.ai.azure.com
Content-Type: application/json
Authorization: Bearer <access_token>
```

### 📋 List All Agents

**Option 1: OpenAI-Compatible Endpoint (Shows general agents)**
- **Endpoint**: `/openai/assistants`
- **API Version**: `2024-02-15-preview`
- **Agents Found**: Various general-purpose assistants

```bash
curl -X GET "https://your-project.services.ai.azure.com/openai/assistants?api-version=2024-02-15-preview" \
  -H "Authorization: Bearer $(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" \
  -H "Content-Type: application/json"
```

**Option 2: Azure AI Foundry Native Endpoint (Shows your custom agent)**
- **Endpoint**: `/api/projects/your-project/assistants`
- **API Version**: `2025-05-01`
- **Agents Found**: Your custom-built assistant

```bash
curl -X GET "https://your-project.services.ai.azure.com/api/projects/your-project/assistants?api-version=2025-05-01" \
  -H "Authorization: Bearer $(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" \
  -H "Content-Type: application/json"
```

**Response for your custom agent:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "asst_your_custom_id",
      "object": "assistant",
      "name": "Custom AI Assistant",
      "description": "",
      "model": "gpt-4.1-mini",
      "instructions": "You provide guidance based on provided data...",
      "tools": [],
      "metadata": {}
    }
  ]
}
```

### 🤖 Get Specific Agent (Your Custom Agent)

```bash
curl -X GET "https://your-project.services.ai.azure.com/api/projects/your-project/assistants/asst_your_custom_id?api-version=2025-05-01" \
  -H "Authorization: Bearer $(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" \
  -H "Content-Type: application/json"
```

### 💬 Create Thread

```bash
curl -X POST "https://your-project.services.ai.azure.com/openai/threads?api-version=2024-02-15-preview" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -d '{}'
```

**Response:**
```json
{
  "id": "thread_example_id",
  "object": "thread",
  "created_at": 1762791354,
  "metadata": {}
}
```

### 📝 Add Message to Thread

```bash
curl -X POST "https://your-project.services.ai.azure.com/openai/threads/{thread_id}/messages?api-version=2024-02-15-preview" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -d '{
    "role": "user",
    "content": "Hello! How can you help me?"
  }'
```

**Response:**
```json
{
  "id": "msg_example_id",
  "object": "thread.message",
  "created_at": 1762791369,
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": {
        "value": "Hello! How can you help me?",
        "annotations": []
      }
    }
  ]
}
```

### 🏃 Create and Run

```bash
curl -X POST "https://your-project.services.ai.azure.com/openai/threads/{thread_id}/runs?api-version=2024-02-15-preview" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -d '{
    "assistant_id": "asst_your_custom_id",
    "instructions": "You are a helpful assistant. Please provide clear and concise answers."
  }'
```

**Response:**
```json
{
  "id": "run_example_id",
  "object": "thread.run",
  "status": "queued",
  "assistant_id": "asst_your_custom_id",
  "thread_id": "thread_example_id"
}
```

### 📊 Check Run Status

```bash
curl -X GET "https://your-project.services.ai.azure.com/openai/threads/{thread_id}/runs/{run_id}?api-version=2024-02-15-preview" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json"
```

**Status Values:**
- `queued` - Run is waiting to start
- `in_progress` - Run is executing
- `completed` - Run finished successfully
- `failed` - Run encountered an error
- `cancelled` - Run was cancelled
- `expired` - Run timed out

### 📨 Get Messages from Thread

```bash
curl -X GET "https://your-project.services.ai.azure.com/openai/threads/{thread_id}/messages?api-version=2024-02-15-preview" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "msg_assistant_response",
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": {
            "value": "Of course! How can I assist you today?",
            "annotations": []
          }
        }
      ]
    }
  ]
}
```

## 🐍 Python SDK Usage

### Installation
```bash
pip install azure-identity requests
# OR for the native SDK (less reliable for Azure AI Foundry)
pip install azure-ai-projects
```

### Direct REST API Approach (Recommended)

```python
import requests
from azure.identity import AzureCliCredential

class AzureAIFoundryClient:
    def __init__(self, endpoint, agent_id):
        self.endpoint = endpoint
        self.agent_id = agent_id
        self.credential = AzureCliCredential()
        self.api_version = "2024-02-15-preview"
        self.threads = {}  # Store thread IDs per session
    
    def get_access_token(self):
        token = self.credential.get_token("https://ai.azure.com/.default")
        return token.token
    
    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2"
        }
    
    def list_agents(self):
        url = f"{self.endpoint}/openai/assistants"
        params = {"api-version": self.api_version}
        response = requests.get(url, headers=self.get_headers(), params=params)
        return response.json()
    
    def create_thread(self, session_id):
        url = f"{self.endpoint}/openai/threads"
        params = {"api-version": self.api_version}
        response = requests.post(url, headers=self.get_headers(), params=params, json={})
        
        if response.status_code == 200:
            thread_data = response.json()
            self.threads[session_id] = thread_data['id']
            return thread_data['id']
        return None
    
    def send_message(self, message, session_id):
        # Get or create thread
        thread_id = self.threads.get(session_id) or self.create_thread(session_id)
        if not thread_id:
            return "Failed to create thread"
        
        headers = self.get_headers()
        params = {"api-version": self.api_version}
        
        # 1. Add message
        message_url = f"{self.endpoint}/openai/threads/{thread_id}/messages"
        message_data = {"role": "user", "content": message}
        requests.post(message_url, headers=headers, params=params, json=message_data)
        
        # 2. Create run
        run_url = f"{self.endpoint}/openai/threads/{thread_id}/runs"
        run_data = {
            "assistant_id": self.agent_id,
            "instructions": "You are a helpful assistant."
        }
        run_response = requests.post(run_url, headers=headers, params=params, json=run_data)
        run_id = run_response.json()['id']
        
        # 3. Wait for completion
        import time
        max_wait = 30
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(1)
            wait_time += 1
            
            status_url = f"{self.endpoint}/openai/threads/{thread_id}/runs/{run_id}"
            status_response = requests.get(status_url, headers=headers, params=params)
            status = status_response.json().get('status')
            
            if status == "completed":
                break
            elif status in ["failed", "cancelled", "expired"]:
                return "Run failed"
        
        # 4. Get messages
        messages_url = f"{self.endpoint}/openai/threads/{thread_id}/messages"
        messages_response = requests.get(messages_url, headers=headers, params=params)
        messages_data = messages_response.json()
        
        # Find latest assistant message
        for message in messages_data.get('data', []):
            if message.get('role') == 'assistant':
                content = message.get('content', [])
                if content and content[0].get('type') == 'text':
                    return content[0]['text']['value']
        
        return "No response received"

# Usage Example - YOUR SPECIFIC AGENT
client = AzureAIFoundryClient(
    endpoint="https://your-project.services.ai.azure.com",
    agent_id="asst_your_custom_id"  # Your custom assistant
)

# List available agents
agents = client.list_agents()
print(f"Available agents: {len(agents['data'])}")

# Send a message
response = client.send_message("Hello! Can you help me?", session_id="user123")
print(f"Agent response: {response}")
```

### Native Azure AI Projects SDK (Limited Support)

```python
from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

# This approach has authentication issues with Azure AI Foundry
credential = AzureCliCredential()
client = AIProjectClient.from_connection_string(
    conn_str="https://your-project.services.ai.azure.com;your-subscription-id;your-resource-group;your-project",
    credential=credential
)

# May fail with 401 Unauthorized due to scope issues
agents = client.agents.list_agents()
```

## ⚠️ Common Issues & Solutions

### 401 Unauthorized
- **Problem**: Wrong authentication scope or method
- **Solution**: Use `https://ai.azure.com/.default` scope with Bearer token

### 400 Bad Request - API Version Not Supported
- **Problem**: Using wrong API version
- **Solution**: Use `2024-02-15-preview`

### 404 Not Found
- **Problem**: Using wrong endpoint pattern
- **Solution**: Use `/openai/assistants` not `/api/projects/.../assistants`

### Agent Not Found
- **Problem**: Using non-existent agent ID
- **Solution**: List agents first to get valid IDs

## 📚 Available Agents

Based on testing, these agents are available:

**Your Custom Agent (Native API):**
1. **Custom AI Assistant** (`asst_your_custom_id`)
   - Specialized assistance for your domain
   - Model: gpt-4.1-mini
   - Provides guidance based on provided data only
   - Access via: `/api/projects/.../assistants` with API version `2025-05-01`

**General Agents (OpenAI-Compatible API):**
1. **General Assistant** (`asst_general_id`)
   - Friendly general assistant
   - Model: gpt-4.1-mini
   - Access via: `/openai/assistants` with API version `2024-02-15-preview`

## 🔧 Working Patterns

### ✅ Correct Patterns

**For your custom agent:**
- Endpoint: `/api/projects/your-project/assistants`
- API Version: `2025-05-01`
- Auth: Bearer token with `https://ai.azure.com/.default`

**For general agents (OpenAI-compatible):**
- Endpoint: `/openai/assistants`
- API Version: `2024-02-15-preview`
- Auth: Bearer token with `https://ai.azure.com/.default`
- Headers: Include `OpenAI-Beta: assistants=v2`

### ❌ Incorrect Patterns
- Endpoint: `/api/projects/.../assistants`
- API Version: `v1` or other versions
- Auth: API keys or subscription keys
- Missing OpenAI-Beta header

## 💡 Best Practices

1. **Cache access tokens** - They're valid for ~1 hour
2. **Handle token refresh** - Implement automatic token renewal
3. **Store thread IDs** - Maintain conversation context per user
4. **Poll run status** - Don't assume instant completion
5. **Handle timeouts** - Implement reasonable wait limits
6. **Error handling** - Graceful fallback for API failures

## 📝 Example Flask Integration

See the working `app.py` file in this repository for a complete Flask integration example that demonstrates:
- Proper authentication flow
- Thread management per user session
- Complete conversation workflow
- Error handling and fallbacks

## 🔗 References

- Azure AI Foundry Documentation
- OpenAI Assistants API Reference
- Azure Identity Library Documentation

---

*Last updated: November 17, 2025*
*Based on testing with Azure AI Foundry OpenAI-compatible APIs*