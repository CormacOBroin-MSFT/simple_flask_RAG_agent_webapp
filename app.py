
import os
import json
import time
import requests
import random
from flask import Flask, render_template, request, jsonify, session
import uuid
from azure.identity import DefaultAzureCredential, AzureCliCredential, ChainedTokenCredential
from config import Config

# Initialize Flask app at the top so it is available for route decorators
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY


class AzureAIClient:
    """Encapsulates Azure AI Foundry client logic and state management"""

    def __init__(self, config_class=Config):
        self.config = config_class
        self.endpoint = config_class.AZURE_AI_PROJECT_ENDPOINT
        self.project_name = config_class.AZURE_AI_PROJECT_NAME
        self.api_version = config_class.AZURE_AI_API_VERSION
        self.agent_id = config_class.AZURE_AI_AGENT_ID
        self.credential = None
        self.access_token = None
        self.conversation_threads = {}

    def get_access_token(self):
        """Get Azure access token for AI Foundry"""
        try:
            # Initialize credential if needed
            if not self.credential:
                self.credential = AzureCliCredential()

            # Get token with correct scope for Azure AI Foundry
            token = self.credential.get_token("https://ai.azure.com/.default")
            self.access_token = token.token

            print(f"✅ Got Azure access token: {self.access_token[:20]}...")
            return self.access_token

        except Exception as e:
            print(f"❌ Failed to get Azure access token: {e}")
            return None

    def _get_headers(self):
        """Get request headers with current token"""
        token = self.get_access_token()
        if not token:
            return None
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _get_params(self):
        """Get common API parameters"""
        return {"api-version": self.api_version}

    def initialize(self):
        """Initialize and test Azure AI Foundry connection"""
        try:
            print(f"🔧 Initializing Azure AI Foundry OpenAI API...")
            print(f"   📡 Endpoint: {self.endpoint}")
            print(f"   🤖 Agent ID: {self.agent_id}")
            print(f"   📋 Project: {self.project_name}")
            print(f"   🔢 API Version: {self.api_version}")

            # Initialize credential
            self.credential = AzureCliCredential()

            # Test authentication
            headers = self._get_headers()
            if not headers:
                print("❌ Could not get access token")
                return False

            # Test if we can list agents using native API
            agents_url = self.config.get_endpoint('assistants')

            response = requests.get(
                agents_url, headers=headers, params=self._get_params())

            if response.status_code == 200:
                agents_data = response.json()
                print(f"   ✅ Found {len(agents_data.get('data', []))} agents")

                # Check if our target agent exists
                for agent in agents_data.get('data', []):
                    if agent['id'] == self.agent_id:
                        print(
                            f"   🎯 Target agent found: {agent.get('name', 'Unknown')}")
                        return True

                print(
                    f"   ⚠️  Target agent {self.agent_id} not found, but API works")
                return True
            elif response.status_code == 401:
                print(f"   ❌ Authentication failed - check your Azure credentials")
                return False
            elif response.status_code == 404:
                print(f"   ❌ Endpoint not found - check your AZURE_AI_PROJECT_ENDPOINT")
                return False
            else:
                print(
                    f"   ❌ API test failed: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error - unable to reach endpoint: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to initialize Azure AI Foundry: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_or_create_thread(self, session_id):
        """Get existing thread or create a new one for the session"""
        try:
            # Check if we have a thread for this session
            if session_id in self.conversation_threads:
                return self.conversation_threads[session_id]

            headers = self._get_headers()
            if not headers:
                print("❌ Could not get authentication headers for thread creation")
                return None

            # Create new thread using native Azure AI Foundry API
            threads_url = self.config.get_endpoint('threads')

            response = requests.post(
                threads_url, headers=headers, params=self._get_params(), json={})

            if response.status_code == 200:
                thread_data = response.json()
                thread_id = thread_data['id']
                self.conversation_threads[session_id] = thread_id
                print(f"✅ Created new thread: {thread_id}")
                return thread_id
            elif response.status_code == 401:
                print(
                    f"❌ Authentication failed when creating thread - token may have expired")
                return None
            else:
                print(
                    f"❌ Failed to create thread: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            print(f"❌ Request timed out while creating thread")
            return None
        except Exception as e:
            print(f"❌ Error managing thread: {e}")
            return None

    def send_message(self, message, thread_id):
        """Send message to Azure AI Foundry agent and get response"""
        try:
            print(f"📤 Sending message to agent {self.agent_id}")

            headers = self._get_headers()
            if not headers:
                return "Failed to authenticate - please check your Azure credentials."

            params = self._get_params()

            # 1. Add message to thread
            messages_url = self.config.get_endpoint('messages', thread_id=thread_id)
            message_data = {"role": "user", "content": message}

            response = requests.post(
                messages_url, headers=headers, params=params, json=message_data)

            if response.status_code != 200:
                if response.status_code == 404:
                    return "Thread not found - your session may have expired. Please refresh the page."
                print(
                    f"❌ Failed to add message: {response.status_code} - {response.text}")
                return f"Failed to send message (HTTP {response.status_code})."

            message_obj = response.json()
            print(f"✅ Message created: {message_obj['id']}")

            # 2. Create and run
            runs_url = self.config.get_endpoint('runs', thread_id=thread_id)
            run_data = {"assistant_id": self.agent_id}

            response = requests.post(
                runs_url, headers=headers, params=params, json=run_data)

            if response.status_code != 200:
                print(
                    f"❌ Failed to create run: {response.status_code} - {response.text}")
                return f"Failed to process request (HTTP {response.status_code})."

            run_obj = response.json()
            run_id = run_obj['id']
            print(f"✅ Run created: {run_id}")

            # 3. Wait for completion
            max_wait = 30
            wait_time = 0

            while wait_time < max_wait:
                time.sleep(1)
                wait_time += 1

                run_status_url = self.config.get_endpoint('run_status', thread_id=thread_id, run_id=run_id)
                response = requests.get(
                    run_status_url, headers=headers, params=params)

                if response.status_code == 200:
                    run_status = response.json()
                    status = run_status.get('status')
                    print(f"🔄 Run status: {status}")

                    if status == "completed":
                        break
                    elif status in ["failed", "cancelled", "expired"]:
                        error_info = run_status.get('last_error', {})
                        error_msg = error_info.get('message', 'Unknown error')
                        print(
                            f"❌ Run failed with status: {status}, error: {error_msg}")
                        return f"Sorry, the request failed: {error_msg}"
                else:
                    print(
                        f"❌ Failed to check run status: {response.status_code}")
                    return "Failed to check processing status."

            if wait_time >= max_wait:
                print("⏰ Run timed out")
                return "Request timed out. The agent is taking longer than expected. Please try again."

            # 4. Get messages
            messages_url = self.config.get_endpoint('messages', thread_id=thread_id)
            response = requests.get(
                messages_url, headers=headers, params=params)

            if response.status_code != 200:
                print(
                    f"❌ Failed to get messages: {response.status_code} - {response.text}")
                return "Failed to retrieve response."

            messages_data = response.json()
            messages = messages_data.get('data', [])

            # Find the latest assistant message
            for msg in messages:
                if msg.get('role') == 'assistant':
                    content = msg.get('content', [])
                    if content and len(content) > 0:
                        text_content = content[0]
                        if text_content.get('type') == 'text':
                            return text_content.get('text', {}).get('value', 'No response content')

            return "I received your message but couldn't generate a proper response."

        except requests.exceptions.Timeout:
            print(f"❌ Request timed out")
            return "The request timed out. Please try again."
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error: {e}")
            return "Unable to connect to Azure AI service. Please check your network connection."
        except Exception as e:
            print(f"❌ Error sending message to agent: {e}")
            import traceback
            traceback.print_exc()
            return f"Sorry, I encountered an error: {str(e)}"

    def get_response(self, user_input, session_id):
        """Get response from Azure AI Foundry Agent"""
        try:
            if not self.credential:
                return "Azure AI not initialized. Please check your configuration."

            # Get or create thread for this session
            thread_id = self.get_or_create_thread(session_id)
            if not thread_id:
                return "Failed to create conversation thread. Please try again."

            # Send message to agent
            response = self.send_message(user_input, thread_id)
            return response

        except Exception as e:
            print(f"❌ Error with Azure AI Foundry Agent: {e}")
            import traceback
            traceback.print_exc()
            return f"Sorry, I encountered an error: {str(e)}"


# Global Azure AI client instance
azure_client = None


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


def get_bot_response(user_input):
    """Get chatbot response - only from Azure AI Foundry Agent, else return debug info"""
    user_input = user_input.strip()

    # Generate session ID if not in session
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    session_id = session['session_id']

    # Only use Azure AI Foundry Agent
    if Config.USE_AZURE_AGENT and azure_client:
        azure_response = azure_client.get_response(user_input, session_id)
        if azure_response and not azure_response.startswith("Failed to create") and not azure_response.startswith("Sorry, I encountered"):
            return azure_response

    # If not available, return debug info
    debug_info = []
    if not Config.USE_AZURE_AGENT:
        debug_info.append(
            "[Debug] Azure AI agent usage is disabled (USE_AZURE_AGENT is false).")
    if not azure_client:
        debug_info.append("[Debug] Azure AI client is not initialized.")
    if not Config.is_azure_configured():
        debug_info.append(
            "[Debug] Azure AI configuration is incomplete or using placeholder values.")
    debug_info.append(
        "[Debug] No fallback responses are enabled. Please check your Azure AI configuration.")
    return '<br>'.join(debug_info)


@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html',
                           bot_name=Config.BOT_NAME,
                           greeting=Config.GREETING_MESSAGE)


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
    azure_configured = bool(azure_client and azure_client.credential)
    agent_configured = bool(Config.AZURE_AI_AGENT_ID and Config.USE_AZURE_AGENT)

    return jsonify({
        'bot_name': Config.BOT_NAME,
        'greeting_message': Config.GREETING_MESSAGE,
        'azure_ai_foundry_enabled': azure_configured,
        'endpoint': Config.AZURE_AI_PROJECT_ENDPOINT if azure_configured else None,
        'project_name': Config.AZURE_AI_PROJECT_NAME if azure_configured else None,
        'agent_mode': agent_configured,
        'agent_id': Config.AZURE_AI_AGENT_ID if agent_configured else None,
        'api_version': Config.AZURE_AI_API_VERSION if azure_configured else None
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    status = {
        'status': 'healthy',
        'azure_ai_foundry_configured': azure_client is not None and azure_client.credential is not None,
        'agent_configured': Config.AZURE_AI_AGENT_ID is not None,
        'agent_mode': Config.USE_AZURE_AGENT
    }
    return jsonify(status)


if __name__ == '__main__':
    print(f"🚀 Starting {Config.BOT_NAME} with Azure AI Foundry Native API")
    print("=" * 60)

    # Initialize Azure AI Foundry client
    print(f"📡 Endpoint: {Config.AZURE_AI_PROJECT_ENDPOINT}")
    print(f"📁 Project: {Config.AZURE_AI_PROJECT_NAME}")
    print(f"🤖 Agent: {Config.AZURE_AI_AGENT_ID}")
    print(f"🔢 API Version: {Config.AZURE_AI_API_VERSION}")

    azure_initialized = False
    if Config.is_azure_configured():
        azure_client = AzureAIClient()
        azure_initialized = azure_client.initialize()
    else:
        print("⚠️  Azure AI Foundry not configured - using placeholder values")
        print("   💡 Set environment variables to enable Azure AI integration")

    if azure_initialized:
        if Config.USE_AZURE_AGENT:
            print(
                f"✅ Azure AI Foundry native agent ready: {Config.AZURE_AI_AGENT_ID}")
        else:
            print(f"⚠️  Azure AI Foundry configured but agent disabled")
    else:
        print(f"❌ Azure AI Foundry initialization failed - using fallback responses")

    print(f"🌐 Starting server on port {Config.PORT}...")
    print(f"🔧 Debug mode: {Config.DEBUG_MODE}")

    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG_MODE)
