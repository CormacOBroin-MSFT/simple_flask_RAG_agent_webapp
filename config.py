"""
Configuration file for Azure AI Foundry Flask Application

This file defines all API endpoints and configuration settings.
You can override these with environment variables.
"""

import os


class Config:
    """Application configuration with endpoint definitions"""

    # Flask Configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')
    DEBUG_MODE = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5000))

    # Azure AI Foundry Configuration
    # Option 1: Hardcode values directly (set these per app)
    AZURE_AI_PROJECT_ENDPOINT = os.environ.get(
        'AZURE_AI_PROJECT_ENDPOINT', 'https://your-resource.services.ai.azure.com/api/projects/your-project')
    AZURE_AI_PROJECT_NAME = os.environ.get(
        'AZURE_AI_PROJECT_NAME', 'your-project')
    AZURE_AI_API_VERSION = os.environ.get('AZURE_AI_API_VERSION', '2025-05-01')
    AZURE_AI_AGENT_ID = os.environ.get(
        'AZURE_AI_AGENT_ID', 'asst_your_agent_id')

    # Agent Configuration
    USE_AZURE_AGENT = os.environ.get(
        'USE_AZURE_AGENT', 'true').lower() == 'true'
    BOT_NAME = os.environ.get('BOT_NAME', 'AI Assistant')
    GREETING_MESSAGE = os.environ.get('GREETING_MESSAGE', '')

    # API Endpoint Definitions
    # You can customize these endpoint patterns or override with environment variables
    ENDPOINT_ASSISTANTS = os.environ.get('ENDPOINT_ASSISTANTS', '/assistants')
    ENDPOINT_THREADS = os.environ.get('ENDPOINT_THREADS', '/threads')
    ENDPOINT_MESSAGES = os.environ.get(
        'ENDPOINT_MESSAGES', '/threads/{thread_id}/messages')
    ENDPOINT_RUNS = os.environ.get(
        'ENDPOINT_RUNS', '/threads/{thread_id}/runs')
    ENDPOINT_RUN_STATUS = os.environ.get(
        'ENDPOINT_RUN_STATUS', '/threads/{thread_id}/runs/{run_id}')

    @classmethod
    def is_azure_configured(cls):
        """Check if all required Azure configuration is set"""
        return all([
            cls.AZURE_AI_PROJECT_ENDPOINT,
            cls.AZURE_AI_PROJECT_NAME,
            cls.AZURE_AI_API_VERSION,
            cls.AZURE_AI_AGENT_ID
        ])

    @classmethod
    def get_endpoint(cls, endpoint_type, **kwargs):
        """
        Get a formatted endpoint URL

        Args:
            endpoint_type: One of 'assistants', 'threads', 'messages', 'runs', 'run_status'
            **kwargs: Variables to format into the endpoint (e.g., thread_id, run_id)

        Returns:
            Full endpoint URL
        """
        base = cls.AZURE_AI_PROJECT_ENDPOINT

        endpoint_map = {
            'assistants': cls.ENDPOINT_ASSISTANTS,
            'threads': cls.ENDPOINT_THREADS,
            'messages': cls.ENDPOINT_MESSAGES,
            'runs': cls.ENDPOINT_RUNS,
            'run_status': cls.ENDPOINT_RUN_STATUS
        }

        path = endpoint_map.get(endpoint_type, '')

        # Format the path with provided variables
        if kwargs:
            path = path.format(**kwargs)

        return f"{base}{path}"
