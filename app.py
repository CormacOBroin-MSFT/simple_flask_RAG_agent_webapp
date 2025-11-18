
import os
import json
import time
import requests
import random
from flask import Flask, render_template, request, jsonify, session
import uuid
from azure.identity import DefaultAzureCredential, AzureCliCredential, ChainedTokenCredential

# Initialize Flask app at the top so it is available for route decorators
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'


# Azure AI Foundry Configuration - Native API Endpoint (must be set in environment)
AZURE_AI_ENDPOINT = os.environ['AZURE_AI_ENDPOINT']
AZURE_AI_PROJECT_NAME = os.environ['AZURE_AI_PROJECT_NAME']
AZURE_AI_API_VERSION = os.environ['AZURE_AI_API_VERSION']
AZURE_AI_AGENT_ID = os.environ['AZURE_AI_AGENT_ID']

# Check if Azure AI is properly configured (all must be set)
AZURE_AI_CONFIGURED = all([
    AZURE_AI_ENDPOINT,
    AZURE_AI_PROJECT_NAME,
    AZURE_AI_API_VERSION,
    AZURE_AI_AGENT_ID
])


# Application Configuration
config = {
    'bot_name': os.environ.get('BOT_NAME', 'AI Assistant'),
    'greeting_message': os.environ.get('GREETING_MESSAGE', ''),
    'debug_mode': os.environ.get('FLASK_DEBUG', 'True').lower() == 'true',
    'port': int(os.environ.get('PORT', 5000)),
    'use_agent': os.environ.get('USE_AZURE_AGENT', 'true').lower() == 'true'
}

# Global dictionary to track conversation threads per session
conversation_threads = {}


def get_azure_access_token():
    """Get Azure access token for AI Foundry"""
    global current_access_token, azure_credential

    try:
        # Initialize credential if needed
        if not azure_credential:
            azure_credential = AzureCliCredential()

        # Get token with correct scope for Azure AI Foundry
        token = azure_credential.get_token("https://ai.azure.com/.default")
        current_access_token = token.token

        print(f"✅ Got Azure access token: {current_access_token[:20]}...")
        return current_access_token

    except Exception as e:
        print(f"❌ Failed to get Azure access token: {e}")
        return None


def initialize_azure_client():
    """Initialize Azure AI Foundry with OpenAI compatible API"""
    global azure_credential

    # Skip initialization if Azure AI is not properly configured
    if not AZURE_AI_CONFIGURED:
        print("⚠️  Azure AI Foundry not configured - using placeholder values")
        print("   💡 Set environment variables to enable Azure AI integration")
        return False

    try:
        print(f"🔧 Initializing Azure AI Foundry OpenAI API...")
        print(f"   📡 Endpoint: {AZURE_AI_ENDPOINT}")
        print(f"   🤖 Agent ID: {AZURE_AI_AGENT_ID}")
        print(f"   📋 Project: {AZURE_AI_PROJECT_NAME}")
        print(f"   � API Version: {AZURE_AI_API_VERSION}")

        # Initialize credential
        azure_credential = AzureCliCredential()

        # Test authentication
        token = get_azure_access_token()
        if not token:
            print("❌ Could not get access token")
            return False

        # Test if we can list agents using native API
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        agents_url = f"{AZURE_AI_ENDPOINT}/api/projects/{AZURE_AI_PROJECT_NAME}/assistants"
        params = {"api-version": AZURE_AI_API_VERSION}

        response = requests.get(agents_url, headers=headers, params=params)

        if response.status_code == 200:
            agents_data = response.json()
            print(f"   ✅ Found {len(agents_data.get('data', []))} agents")

            # Check if our target agent exists
            for agent in agents_data.get('data', []):
                if agent['id'] == AZURE_AI_AGENT_ID:
                    print(
                        f"   🎯 Target agent found: {agent.get('name', 'Unknown')}")
                    return True

            print(
                f"   ⚠️  Target agent {AZURE_AI_AGENT_ID} not found, but API works")
            return True
        else:
            print(
                f"   ❌ API test failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Failed to initialize Azure AI Foundry: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_or_create_thread(session_id):
    """Get existing thread or create a new one for the session"""
    global conversation_threads

    try:
        # Check if we have a thread for this session
        if session_id in conversation_threads:
            return conversation_threads[session_id]

        # Get current token
        token = get_azure_access_token()
        if not token:
            return None

        # Create new thread using native Azure AI Foundry API
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        threads_url = f"{AZURE_AI_ENDPOINT}/api/projects/{AZURE_AI_PROJECT_NAME}/threads"
        params = {"api-version": AZURE_AI_API_VERSION}

        response = requests.post(
            threads_url, headers=headers, params=params, json={})

        if response.status_code == 200:
            thread_data = response.json()
            thread_id = thread_data['id']
            conversation_threads[session_id] = thread_id
            print(f"✅ Created new thread: {thread_id}")
            return thread_id
        else:
            print(
                f"❌ Failed to create thread: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error managing thread: {e}")
        return None


def send_message_to_agent(message, thread_id):
    """Send message to Azure AI Foundry agent using OpenAI compatible API"""
    try:
        print(f"📤 Sending message to agent {AZURE_AI_AGENT_ID}")

        # Get current token
        token = get_azure_access_token()
        if not token:
            return "Failed to get authentication token."

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {"api-version": AZURE_AI_API_VERSION}

        # 1. Add message to thread using native API
        messages_url = f"{AZURE_AI_ENDPOINT}/api/projects/{AZURE_AI_PROJECT_NAME}/threads/{thread_id}/messages"
        message_data = {
            "role": "user",
            "content": message
        }

        response = requests.post(
            messages_url, headers=headers, params=params, json=message_data)

        if response.status_code != 200:
            print(
                f"❌ Failed to add message: {response.status_code} - {response.text}")
            return "Failed to send message."

        message_obj = response.json()
        print(f"✅ Message created: {message_obj['id']}")

        # 2. Create and run using native API
        runs_url = f"{AZURE_AI_ENDPOINT}/api/projects/{AZURE_AI_PROJECT_NAME}/threads/{thread_id}/runs"
        run_data = {
            "assistant_id": AZURE_AI_AGENT_ID,
            # "instructions": "You are a helpful assistant. Please provide clear and concise answers."
        }

        response = requests.post(
            runs_url, headers=headers, params=params, json=run_data)

        if response.status_code != 200:
            print(
                f"❌ Failed to create run: {response.status_code} - {response.text}")
            return "Failed to process request."

        run_obj = response.json()
        run_id = run_obj['id']
        print(f"✅ Run created: {run_id}")

        # 3. Wait for completion
        max_wait = 30  # 30 seconds max
        wait_time = 0

        while wait_time < max_wait:
            time.sleep(1)
            wait_time += 1

            # Check run status using native API
            run_status_url = f"{AZURE_AI_ENDPOINT}/api/projects/{AZURE_AI_PROJECT_NAME}/threads/{thread_id}/runs/{run_id}"
            response = requests.get(
                run_status_url, headers=headers, params=params)

            if response.status_code == 200:
                run_status = response.json()
                status = run_status.get('status')
                print(f"🔄 Run status: {status}")

                if status == "completed":
                    break
                elif status in ["failed", "cancelled", "expired"]:
                    print(f"❌ Run failed with status: {status}")
                    return "Sorry, I encountered an error processing your request."
            else:
                print(f"❌ Failed to check run status: {response.status_code}")
                return "Failed to check processing status."

        if wait_time >= max_wait:
            print("⏰ Run timed out")
            return "Request timed out. Please try again."

        # 4. Get messages using native API
        messages_url = f"{AZURE_AI_ENDPOINT}/api/projects/{AZURE_AI_PROJECT_NAME}/threads/{thread_id}/messages"
        response = requests.get(messages_url, headers=headers, params=params)

        if response.status_code != 200:
            print(
                f"❌ Failed to get messages: {response.status_code} - {response.text}")
            return "Failed to retrieve response."

        messages_data = response.json()
        messages = messages_data.get('data', [])

        # Find the latest assistant message
        for message in messages:
            if message.get('role') == 'assistant':
                content = message.get('content', [])
                if content and len(content) > 0:
                    text_content = content[0]
                    if text_content.get('type') == 'text':
                        return text_content.get('text', {}).get('value', 'No response content')

        return "I received your message but couldn't generate a proper response."

    except Exception as e:
        print(f"❌ Error sending message to agent: {e}")
        import traceback
        traceback.print_exc()
        return f"Sorry, I encountered an error: {str(e)}"


def get_azure_agent_response(user_input, session_id):
    """Get response from Azure AI Foundry Agent using OpenAI compatible API"""
    try:
        if not azure_credential:
            return "Azure AI not initialized. Please check your configuration."

        # Get or create thread for this session
        thread_id = get_or_create_thread(session_id)
        if not thread_id:
            return "Failed to create conversation thread."

        # Send message to agent
        response = send_message_to_agent(user_input, thread_id)
        return response

    except Exception as e:
        print(f"❌ Error with Azure AI Foundry Agent: {e}")
        import traceback
        traceback.print_exc()
        return f"Sorry, I encountered an error: {str(e)}"


def format_response_text(text):
    """Format response text with proper line breaks and markdown"""
    if not text:
        return ""

    # Convert newlines to HTML line breaks for better formatting
    formatted = text.replace('\n', '<br>')

    # Handle markdown-style formatting
    import re

    # Bold text (**text** or __text__)
    formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted)
    formatted = re.sub(r'__(.*?)__', r'<strong>\1</strong>', formatted)

    # Italic text (*text* or _text_)
    formatted = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted)
    formatted = re.sub(r'_(.*?)_', r'<em>\1</em>', formatted)

    # Code blocks (```code```)
    formatted = re.sub(
        r'```(.*?)```', r'<code class="code-block">\1</code>', formatted, flags=re.DOTALL)

    # Inline code (`code`)
    formatted = re.sub(
        r'`(.*?)`', r'<code class="inline-code">\1</code>', formatted)

    return formatted


# Restore get_bot_response as a standalone function
def get_bot_response(user_input):
    """Get chatbot response - only from Azure AI Foundry Agent, else return debug info"""
    user_input = user_input.strip()

    # Generate session ID if not in session
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    session_id = session['session_id']

    # Only use Azure AI Foundry Agent
    if config['use_agent'] and azure_credential:
        azure_response = get_azure_agent_response(user_input, session_id)
        if azure_response and not azure_response.startswith("Failed to create") and not azure_response.startswith("Sorry, I encountered"):
            return azure_response

    # If not available, return debug info
    debug_info = []
    if not config['use_agent']:
        debug_info.append(
            "[Debug] Azure AI agent usage is disabled (USE_AZURE_AGENT is false).")
    if not azure_credential:
        debug_info.append("[Debug] Azure credential is not initialized.")
    if not AZURE_AI_CONFIGURED:
        debug_info.append(
            "[Debug] Azure AI configuration is incomplete or using placeholder values.")
    debug_info.append(
        "[Debug] No fallback responses are enabled. Please check your Azure AI configuration.")
    return '<br>'.join(debug_info)


@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html',
                           bot_name=config['bot_name'],
                           greeting=config['greeting_message'])


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        print(f"👤 User: {user_message}")

        # Get bot response
        bot_response = get_bot_response(user_message)

        print(f"🤖 Bot: {bot_response}")

        return jsonify({
            'response': format_response_text(bot_response),
            'user_message': user_message
        })

    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500


@app.route('/config')
def get_config():
    """Get current bot configuration"""
    azure_configured = bool(azure_credential)
    agent_configured = bool(AZURE_AI_AGENT_ID and config['use_agent'])

    return jsonify({
        'bot_name': config['bot_name'],
        'greeting_message': config['greeting_message'],
        'azure_ai_foundry_enabled': azure_configured,
        'endpoint': AZURE_AI_ENDPOINT if azure_configured else None,
        'project_name': AZURE_AI_PROJECT_NAME if azure_configured else None,
        'agent_mode': agent_configured,
        'agent_id': AZURE_AI_AGENT_ID if agent_configured else None,
        'api_version': AZURE_AI_API_VERSION if azure_configured else None
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    status = {
        'status': 'healthy',
        'azure_ai_foundry_configured': azure_credential is not None,
        'agent_configured': AZURE_AI_AGENT_ID is not None,
        'agent_mode': config['use_agent']
    }
    return jsonify(status)


if __name__ == '__main__':
    print(f"🚀 Starting {config['bot_name']} with Azure AI Foundry Native API")
    print("=" * 60)

    # Initialize Azure AI Foundry client
    print(f"📡 Endpoint: {AZURE_AI_ENDPOINT}")
    print(f"📁 Project: {AZURE_AI_PROJECT_NAME}")
    print(f"🤖 Agent: {AZURE_AI_AGENT_ID}")
    print(f"🔢 API Version: {AZURE_AI_API_VERSION}")

    azure_initialized = initialize_azure_client()

    if azure_initialized:
        if config['use_agent']:
            print(
                f"✅ Azure AI Foundry native agent ready: {AZURE_AI_AGENT_ID}")
        else:
            print(f"⚠️  Azure AI Foundry configured but agent disabled")
    else:
        print(f"❌ Azure AI Foundry initialization failed - using fallback responses")

    print(f"🌐 Starting server on port {config['port']}...")
    print(f"🔧 Debug mode: {config['debug_mode']}")

    app.run(host='0.0.0.0', port=config['port'], debug=config['debug_mode'])
