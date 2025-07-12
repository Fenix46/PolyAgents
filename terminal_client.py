"""
A terminal-based client for interacting with the PolyAgents API.

This client connects to the WebSocket endpoint to provide a real-time,
interactive chat experience from your terminal.

Usage:
  - Ensure you have a .env file with API_HOST, API_PORT, and an API key.
  - Run the script: python terminal_client.py
"""

import asyncio
import aiohttp
import websockets
import os
import json
from dotenv import load_dotenv
from uuid import uuid4
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TerminalClient:
    """An interactive terminal client for the PolyAgents system."""

    def __init__(self, api_host: str, api_port: int, api_key: str):
        self.api_base_url = f"http://{api_host}:{api_port}"
        self.ws_base_url = f"ws://{api_host}:{api_port}"
        self.api_key = api_key
        self.session = aiohttp.ClientSession(headers={"Authorization": f"Bearer {self.api_key}"})

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def start_chat(self):
        """Starts the interactive chat session."""
        print("PolyAgents Terminal Client")
        print("--------------------------")
        print("Type your message and press Enter. Type 'exit' or 'quit' to end.")

        while True:
            try:
                prompt = await asyncio.to_thread(input, "\nYou: ")
                if prompt.lower() in ["exit", "quit"]:
                    break

                if not prompt.strip():
                    continue

                conversation_id = str(uuid4())
                print(f"SYSTEM: Starting new conversation (ID: {conversation_id})")

                await self._handle_conversation(prompt, conversation_id)

            except (KeyboardInterrupt, EOFError):
                break

        print("\nClient shutting down. Goodbye!")

    async def _handle_conversation(self, prompt: str, conversation_id: str):
        """Manages a single conversation, from initial POST to WebSocket communication."""
        ws_url = f"{self.ws_base_url}/ws/{conversation_id}"

        try:
            async with websockets.connect(ws_url, additional_headers={"Authorization": f"Bearer {self.api_key}"}) as websocket:
                # First, send the initial prompt via HTTP to start the process
                await self._trigger_streaming_chat(prompt, conversation_id)
                
                # Then, listen for real-time updates
                await self._listen_for_updates(websocket)

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"\nSYSTEM: Connection closed unexpectedly: {e}")
        except aiohttp.ClientError as e:
            print(f"\nSYSTEM: HTTP Error: {e}")
        except Exception as e:
            print(f"\nSYSTEM: An unexpected error occurred: {e}")

    async def _trigger_streaming_chat(self, prompt: str, conversation_id: str):
        """Sends the initial HTTP POST request to start the streaming conversation."""
        url = f"{self.api_base_url}/stream/{conversation_id}"
        payload = {"message": prompt}
        
        # This request is "fire-and-forget" from the client's perspective.
        # It triggers the backend to start processing and sending updates to the WebSocket.
        async def post_request():
            try:
                async with self.session.post(url, json=payload) as response:
                    if response.status != 202:
                        error_text = await response.text()
                        print(f"\nSYSTEM: Error starting chat: {response.status} {error_text}")
            except Exception as e:
                print(f"\nSYSTEM: Failed to trigger chat: {e}")

        asyncio.create_task(post_request())

    async def _listen_for_updates(self, websocket):
        """Listens for and processes incoming messages from the WebSocket."""
        print("SYSTEM: Waiting for responses...")
        final_answer_received = False
        while not final_answer_received:
            try:
                message_json = await websocket.recv()
                message = json.loads(message_json)
                
                msg_type = message.get("type")
                if msg_type == "message":
                    self._print_message(message.get("message", {}))
                elif msg_type == "turn_started":
                    print(f"\n--- Turn {message.get('turn')} ---")
                elif msg_type == "consensus_started":
                    print("\n--- Consensus Phase ---")
                elif msg_type == "final_answer":
                    self._print_final_answer(message)
                    final_answer_received = True
                else:
                    # Generic print for other event types
                    print(f"SYSTEM: Received event '{msg_type}'")

            except websockets.exceptions.ConnectionClosed:
                print("\nSYSTEM: WebSocket connection closed by server.")
                break
    
    def _print_message(self, msg: dict):
        """Formats and prints a regular message."""
        sender = msg.get('sender', 'unknown')
        content = msg.get('content', '')
        if sender.startswith("agent_"):
            print(f"\nAgent ({sender}):\n{content}")
        elif sender == "user":
            # User message is already displayed, so we can ignore this echo
            pass
        else:
            print(f"\n{sender.upper()}:\n{content}")
            
    def _print_final_answer(self, msg: dict):
        """Formats and prints the final consensus answer."""
        content = msg.get('final_answer', 'No final answer was provided.')
        print("\n==========================")
        print("Final Consensus Answer:")
        print("==========================")
        print(content)
        print("==========================")
        print("SYSTEM: Conversation finished. You can start a new one.")


async def main():
    """Main function to run the client."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "localhost")
    api_port = int(os.getenv("API_PORT", "8000"))
    
    # Try to get one of the default API keys from the environment
    default_keys_json = os.getenv("DEFAULT_API_KEYS")
    api_key = None
    if default_keys_json:
        try:
            keys = json.loads(default_keys_json)
            if keys:
                # Use the first key found
                api_key = keys[0].get("key")
        except json.JSONDecodeError:
            print("Warning: Could not parse DEFAULT_API_KEYS from .env file.")

    if not api_key:
        print("Error: No API key found. Please set DEFAULT_API_KEYS in your .env file.")
        print('Example: DEFAULT_API_KEYS=[{"name":"test-user","key":"your-key-here","permissions":["read","write"]}]')
        return

    async with TerminalClient(api_host, api_port, api_key) as client:
        await client.start_chat()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClient interrupted. Exiting.") 