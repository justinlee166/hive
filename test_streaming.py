#!/usr/bin/env python3
"""
Enhanced test script to verify streaming chat with typing indicators and randomized order
"""

import requests
import json
import time

def test_streaming_endpoint():
    url = "http://127.0.0.1:8000/chat-stream"
    payload = {
        "message": "Hello Hive! What are your thoughts on artificial intelligence?",
        "temperature": 0.7
    }
    
    print("🚀 Testing enhanced streaming chat endpoint...")
    print(f"📝 Sending message: {payload['message']}")
    print("🔄 Testing typing indicators and randomized agent order")
    print("=" * 60)
    
    agent_order = []
    
    try:
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            event_data = json.loads(line_str[6:])
                            
                            if event_data.get('event') == 'complete':
                                print("\n✅ Stream completed!")
                                break
                            
                            agent = event_data.get('agent', 'unknown')
                            content = event_data.get('content', '')
                            status = event_data.get('status')
                            
                            if status == 'typing':
                                print(f"\n💭 {agent.upper()} is typing...")
                                agent_order.append(agent)
                            elif status == 'done':
                                print(f"✅ {agent.upper()} finished:")
                                print(f"💬 {content}")
                                print("-" * 40)
                            elif not status:  # User message or legacy event
                                print(f"\n👤 {agent.upper()}:")
                                print(f"💬 {content}")
                                print("-" * 40)
                            
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON decode error: {e}")
                            continue
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure FastAPI is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Verify randomization by showing agent order
    if agent_order:
        print(f"\n🎲 Agent speaking order: {' → '.join([a.title() for a in agent_order])}")
        print("🔄 Run again to see different random orders!")

def test_multiple_rounds():
    """Test multiple conversations to verify randomization"""
    print("\n🎯 Testing randomization across multiple conversations...")
    orders = []
    
    for i in range(3):
        print(f"\nRound {i+1}:")
        url = "http://127.0.0.1:8000/chat-stream"
        payload = {
            "message": f"Quick test #{i+1}",
            "temperature": 0.7
        }
        
        round_order = []
        
        try:
            with requests.post(url, json=payload, stream=True) as response:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                event_data = json.loads(line_str[6:])
                                if event_data.get('status') == 'typing':
                                    agent = event_data.get('agent')
                                    round_order.append(agent)
                                elif event_data.get('event') == 'complete':
                                    break
                            except:
                                continue
        except:
            continue
        
        if round_order:
            orders.append(' → '.join([a.title() for a in round_order]))
            print(f"  Order: {orders[-1]}")
    
    print(f"\n📊 Randomization results:")
    for i, order in enumerate(orders, 1):
        print(f"  Round {i}: {order}")
    
    unique_orders = len(set(orders))
    print(f"🎲 {unique_orders}/{len(orders)} unique orders - {'✅ Good randomization!' if unique_orders > 1 else '⚠️ May need more tests'}")

if __name__ == "__main__":
    print("🧪 Running enhanced streaming tests...\n")
    test_streaming_endpoint()
    test_multiple_rounds() 