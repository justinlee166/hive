#!/usr/bin/env python3
"""
Test script to verify WebSocket connection and multi-turn autonomous discussions
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws-chat"
    
    print("🚀 Testing WebSocket connection with multi-turn discussions...")
    print(f"📍 Connecting to: {uri}")
    print("=" * 70)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Send a test message
            test_message = {
                "message": "What are the most important considerations for implementing AI in healthcare?",
                "temperature": 0.7
            }
            
            print(f"📤 Sending: {test_message['message']}")
            await websocket.send(json.dumps(test_message))
            
            # Listen for responses
            message_count = 0
            agent_order = []
            current_round = 1
            autonomous_rounds = 0
            
            print("\n🎭 CONVERSATION FLOW:")
            print("=" * 50)
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_count += 1
                    
                    agent = data.get('agent', 'unknown')
                    content = data.get('content', '')
                    status = data.get('status')
                    
                    # Handle different message types
                    if status == 'typing':
                        print(f"💭 {agent.upper()} is thinking...")
                        if agent not in agent_order:
                            agent_order.append(agent)
                            
                    elif status == 'done':
                        print(f"✅ {agent.upper()}:")
                        print(f"   💬 {content}")
                        print()
                        
                        # Detect if this might be an autonomous round
                        if message_count > 8:  # After initial responses
                            autonomous_rounds += 1
                            
                    elif status == 'awaiting_user':
                        print("⏸️  AUTONOMOUS DISCUSSION COMPLETE")
                        print(f"🎯 {data.get('message', 'Agents are waiting for user input')}")
                        print(f"📊 Total autonomous responses: ~{autonomous_rounds}")
                        print("\n✅ Multi-turn test completed successfully!")
                        break
                        
                    elif not status:  # User message or no status
                        if agent == 'user':
                            print(f"👤 {agent.upper()}:")
                            print(f"   💬 {content}")
                            print("\n🤖 INITIAL AGENT RESPONSES:")
                            print("-" * 30)
                        else:
                            print(f"✅ {agent.upper()}:")
                            print(f"   💬 {content}")
                            print()
                    
                    # Safety timeout for very long conversations
                    if message_count >= 25:
                        print("⏰ Test timeout - conversation is very active!")
                        break
                        
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON received: {message}")
                    continue
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    continue
            
            print(f"\n📈 CONVERSATION SUMMARY:")
            print(f"🎲 Initial agent order: {' → '.join([a.title() for a in agent_order if a != 'user'])}")
            print(f"💬 Total messages processed: {message_count}")
            print(f"🔄 Estimated autonomous rounds: {autonomous_rounds // 3 if autonomous_rounds > 0 else 0}")
            print("🔄 Run again to see different random orders and autonomous discussions!")
            
    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure the FastAPI server is running:")
        print("   cd app && uvicorn main:app --reload --host 127.0.0.1 --port 8000")
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

async def test_multiple_user_interactions():
    """Test multiple user messages to see how agents continue discussions"""
    uri = "ws://127.0.0.1:8000/ws-chat"
    
    print("\n" + "="*70)
    print("🔄 TESTING MULTIPLE USER INTERACTIONS")
    print("="*70)
    
    user_messages = [
        "Tell me about renewable energy",
        "What about the economic challenges?",
        "How can we overcome those challenges?"
    ]
    
    try:
        async with websockets.connect(uri) as websocket:
            for i, user_msg in enumerate(user_messages, 1):
                print(f"\n🔸 USER INTERACTION {i}/{len(user_messages)}")
                print(f"📤 Sending: {user_msg}")
                
                await websocket.send(json.dumps({
                    "message": user_msg,
                    "temperature": 0.7
                }))
                
                # Wait for the autonomous discussion to complete
                response_count = 0
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        data = json.loads(message)
                        
                        if data.get('status') == 'awaiting_user':
                            print(f"✅ Interaction {i} complete - agents finished discussing")
                            break
                            
                        response_count += 1
                        
                        # Safety check
                        if response_count > 20:
                            print("⏰ Moving to next interaction...")
                            break
                            
                    except asyncio.TimeoutError:
                        print("⏰ Timeout waiting for response")
                        break
                    except json.JSONDecodeError:
                        continue
                
                # Brief pause between interactions
                await asyncio.sleep(1)
            
            print("\n✅ Multiple interaction test completed!")
            
    except Exception as e:
        print(f"❌ Multiple interaction test failed: {e}")

if __name__ == "__main__":
    print("🧪 RUNNING ENHANCED WEBSOCKET TESTS...\n")
    asyncio.run(test_websocket())
    asyncio.run(test_multiple_user_interactions()) 