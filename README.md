# AI Chatbot Integration Guide

## ⚠️ Security Notice - Development Only

**This application is NOT production-ready and contains security vulnerabilities:**

- **Hardcoded Flask Secret Key**: The session secret key is hardcoded in `app.py` as `'your-secret-key-here'`, which is insecure. This means:
  - Session data can be easily forged or tampered with
  - All deployments share the same key, compromising security across instances
  - Sessions persist across server restarts, which could be exploited

**For production deployment, you MUST:**
1. Generate a secure random secret key: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Set it as an environment variable: `export FLASK_SECRET_KEY="your-generated-key"`
3. Update `app.py` to use: `app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'fallback-dev-key')`

**This application is intended for local development and testing purposes only.**

---

## ☁️ Deploying Your Agent in Azure AI Foundry

To use this chatbot, you must deploy an agent (assistant) in Azure AI Foundry:

1. **Create or select an agent in Azure AI Foundry.**
2. **Add the contents of `agent_instructions.md` to the agent's "System Instructions" field.**
  - This ensures the agent is grounded and will only use information from user-uploaded product data sheets and documents, as described in `agent_instructions.md`.
3. **Upload or provide any additional product data sheets or documents you want the agent to use.**
4. **Configure your environment variables (see below) with the correct agent ID and endpoint.**

> **Important:** The agent will only behave as intended if you copy the full contents of `agent_instructions.md` into the "System Instructions" of your Azure AI Foundry agent. This is required for proper grounding and compliance.

For more details, see the Azure AI Foundry documentation on creating and configuring assistants.

## 🚀 Quick Setup

### 1. Prerequisites
- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)
- Azure CLI (for authentication)

### 2. Clone and Install
```bash
git clone <your-repo-url>
cd simple_flask_RAG_agent_webapp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables
Set the following environment variables (in your shell, `.env`, or `.bashrc`):
- `AZURE_AI_PROJECT_ENDPOINT` - Full project endpoint including path (e.g. `https://your-endpoint.services.ai.azure.com/api/projects/your-project`)
- `AZURE_AI_PROJECT_NAME` - Your project name (e.g. `your-project`)
- `AZURE_AI_API_VERSION` - API version to use (e.g. `2025-05-01`)
- `AZURE_AI_AGENT_ID` - Your assistant ID (e.g. `asst_xxxxx`)
- `USE_AZURE_AGENT` - Set to `true` to enable agent (default: `true`)
- `BOT_NAME` - Optional, UI display name (default: `AI Assistant`)
- `GREETING_MESSAGE` - Optional, UI greeting message
- `FLASK_SECRET_KEY` - Recommended for session security

Example for bash:
```bash
export AZURE_AI_PROJECT_ENDPOINT="https://your-endpoint.services.ai.azure.com/api/projects/your-project"
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

This application uses the **Azure AI Foundry Native API** pattern:

### Base Configuration
```
Project Endpoint: https://your-endpoint.services.ai.azure.com/api/projects/your-project
API Version: 2025-05-01
Content-Type: application/json
Authorization: Bearer <access_token>
```

**Important:** The `AZURE_AI_PROJECT_ENDPOINT` already includes the full path `/api/projects/your-project`, so API calls simply append the resource path (e.g., `/assistants`, `/threads`).

### 📋 List All Agents

**Azure AI Foundry Native Endpoint:**
- **Full URL**: `{AZURE_AI_PROJECT_ENDPOINT}/assistants`
- **API Version**: `2025-05-01` (or your configured version)
- **Agents Found**: Your custom-built assistants in this project

```bash
# Get your project endpoint
PROJECT_ENDPOINT="https://your-endpoint.services.ai.azure.com/api/projects/your-project"
API_VERSION="2025-05-01"

curl -X GET "${PROJECT_ENDPOINT}/assistants?api-version=${API_VERSION}" \
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
PROJECT_ENDPOINT="https://your-endpoint.services.ai.azure.com/api/projects/your-project"
API_VERSION="2025-05-01"
AGENT_ID="asst_your_custom_id"

curl -X GET "${PROJECT_ENDPOINT}/assistants/${AGENT_ID}?api-version=${API_VERSION}" \
  -H "Authorization: Bearer $(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" \
  -H "Content-Type: application/json"
```

### 💬 Create Thread

```bash
PROJECT_ENDPOINT="https://your-endpoint.services.ai.azure.com/api/projects/your-project"
API_VERSION="2025-05-01"

curl -X POST "${PROJECT_ENDPOINT}/threads?api-version=${API_VERSION}" \
  -H "Authorization: Bearer $(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" \
  -H "Content-Type: application/json" \
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
PROJECT_ENDPOINT="https://your-endpoint.services.ai.azure.com/api/projects/your-project"
API_VERSION="2025-05-01"
THREAD_ID="thread_xxxxx"

curl -X POST "${PROJECT_ENDPOINT}/threads/${THREAD_ID}/messages?api-version=${API_VERSION}" \
  -H "Authorization: Bearer $(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" \
  -H "Content-Type: application/json" \
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
PROJECT_ENDPOINT="https://your-endpoint.services.ai.azure.com/api/projects/your-project"
API_VERSION="2025-05-01"
THREAD_ID="thread_xxxxx"
AGENT_ID="asst_your_custom_id"

curl -X POST "${PROJECT_ENDPOINT}/threads/${THREAD_ID}/runs?api-version=${API_VERSION}" \
  -H "Authorization: Bearer $(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "'${AGENT_ID}'"
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
PROJECT_ENDPOINT="https://your-endpoint.services.ai.azure.com/api/projects/your-project"
API_VERSION="2025-05-01"
THREAD_ID="thread_xxxxx"
RUN_ID="run_xxxxx"

curl -X GET "${PROJECT_ENDPOINT}/threads/${THREAD_ID}/runs/${RUN_ID}?api-version=${API_VERSION}" \
  -H "Authorization: Bearer $(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" \
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
PROJECT_ENDPOINT="https://your-endpoint.services.ai.azure.com/api/projects/your-project"
API_VERSION="2025-05-01"
THREAD_ID="thread_xxxxx"

curl -X GET "${PROJECT_ENDPOINT}/threads/${THREAD_ID}/messages?api-version=${API_VERSION}" \
  -H "Authorization: Bearer $(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" \
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


## ⚠️ Common Issues & Solutions

### 401 Unauthorized
- **Problem**: Wrong authentication scope or expired token
- **Solution**: Use `https://ai.azure.com/.default` scope with Bearer token. Ensure you're logged in with `az login`

### 404 Not Found - Resource not found
- **Problem**: Incorrect endpoint URL - likely duplicating the project path
- **Solution**: Ensure `AZURE_AI_PROJECT_ENDPOINT` already includes `/api/projects/your-project`. Don't append it again.
- **Example**: Use `${ENDPOINT}/assistants` NOT `${ENDPOINT}/api/projects/your-project/assistants`

### 404 Not Found - Agent Not Found
- **Problem**: Using non-existent agent ID or wrong project
- **Solution**: List agents first to get valid IDs for your specific project

### Thread/Session Expired
- **Problem**: Thread ID no longer valid
- **Solution**: Create a new thread. The app handles this automatically per user session.

## 📚 Available Agents

Agents available depend on your Azure AI Foundry project. List them using:

```bash
PROJECT_ENDPOINT="your-endpoint-here"
API_VERSION="2025-05-01"
curl -X GET "${PROJECT_ENDPOINT}/assistants?api-version=${API_VERSION}" \
  -H "Authorization: Bearer $(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" \
  -H "Content-Type: application/json"
```

Example agents you might see:
1. **Your Custom Assistant** (`asst_xxxxx`)
   - Specialized for your use case
   - Model: gpt-4.1-mini or other configured model
   - Custom instructions and tools

## 🔧 Working Patterns

### ✅ Correct Patterns

**Azure AI Foundry Native API (used by this app):**
- **Project Endpoint**: `https://your-endpoint.services.ai.azure.com/api/projects/your-project` (full path)
- **Resource Paths**: Append directly - `/assistants`, `/threads`, `/threads/{id}/messages`
- **API Version**: `2025-05-01` (or your configured version)
- **Auth**: Bearer token with `https://ai.azure.com/.default` scope
- **Headers**: `Content-Type: application/json`, `Authorization: Bearer {token}`
- **No OpenAI-Beta header needed**

### ❌ Incorrect Patterns
- **DON'T** duplicate the project path: `{endpoint}/api/projects/{project}/assistants` ❌
- **DON'T** use OpenAI-compatible endpoints: `/openai/assistants` ❌  
- **DON'T** use older API versions unless specifically required
- **DON'T** use API keys or subscription keys - use Azure CLI credential

## 💡 Best Practices

1. **Cache access tokens** - They're valid for ~1 hour, refresh before expiration
2. **Handle token refresh** - The app automatically gets a fresh token for each request
3. **Store thread IDs** - Maintain conversation context per user session (Flask session-based)
4. **Poll run status** - Wait for completion before retrieving messages (max 30 seconds)
5. **Handle timeouts** - Implement reasonable wait limits with user-friendly messages
6. **Error handling** - Specific error messages for different failure scenarios (401, 404, timeout, connection errors)
7. **Use full project endpoint** - Set `AZURE_AI_PROJECT_ENDPOINT` with the complete path including `/api/projects/your-project`

## 📝 Example Flask Integration

See the working `app.py` file in this repository for a complete Flask integration example that demonstrates:
- Class-based Azure AI client with encapsulated logic
- Proper authentication flow using Azure CLI credentials
- Thread management per user session
- Complete conversation workflow (create thread → add message → run → poll → get response)
- Comprehensive error handling with specific messages
- Automatic token refresh

## 🔗 References

- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [Azure Identity Library Documentation](https://learn.microsoft.com/en-us/python/api/azure-identity/)
- [Azure AI Agents Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/develop/agents)

---

*Last updated: November 18, 2025*
*Based on Azure AI Foundry Native API (API Version: 2025-05-01)*