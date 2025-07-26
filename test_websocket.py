#!/usr/bin/env python3
"""
Test script to verify WebSocket connection to the Hive backend
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws-chat"
    
    print("🚀 Testing WebSocket connection to Hive backend...")
    print(f"📍 Connecting to: {uri}")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Send a test message
            test_message = {
                "message": "Hello Hive! Tell me about artificial intelligence.",
                "temperature": 0.7
            }
            
            print(f"📤 Sending: {test_message['message']}")
            await websocket.send(json.dumps(test_message))
            
            # Listen for responses
            message_count = 0
            agent_order = []
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_count += 1
                    
                    agent = data.get('agent', 'unknown')
                    content = data.get('content', '')
                    status = data.get('status')
                    
                    if status == 'typing':
                        print(f"\n💭 {agent.upper()} is typing...")
                        if agent not in agent_order:
                            agent_order.append(agent)
                    elif status == 'done':
                        print(f"✅ {agent.upper()} finished:")
                        print(f"💬 {content}")
                        print("-" * 40)
                    elif not status:  # User message or no status
                        print(f"\n👤 {agent.upper()}:")
                        print(f"💬 {content}")
                        print("-" * 40)
                    
                    # Stop after getting responses from all agents
                    if message_count >= 7:  # User + 3 agents (typing + done each)
                        break
                        
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON received: {message}")
                    continue
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    continue
            
            print(f"\n🎲 Agent speaking order: {' → '.join([a.title() for a in agent_order if a != 'user'])}")
            print("🔄 Run again to see different random orders!")
            print("\n✅ WebSocket test completed successfully!")
            
    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure the FastAPI server is running:")
        print("   cd app && uvicorn main:app --reload --host 127.0.0.1 --port 8000")
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 