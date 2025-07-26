#!/usr/bin/env python3
"""
Test script to verify concise multi-turn discussions with parameterized rounds
"""

import asyncio
import websockets
import json
import time

async def test_no_self_labeling():
    """Test specifically for the self-labeling issue"""
    uri = "ws://127.0.0.1:8000/ws-chat"
    
    print("🚀 Testing NO SELF-LABELING Issue")
    print(f"📍 Connecting to: {uri}")
    print("=" * 70)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Test with a simple question
            test_message = {
                "message": "How can I improve at Valorant?",
                "temperature": 0.7,
                "autonomous_rounds": 2  # Keep it short for testing
            }
            
            print(f"📤 Sending: {test_message['message']}")
            print("\n🎭 CHECKING FOR NATURAL RESPONSES:")
            print("=" * 50)
            
            await websocket.send(json.dumps(test_message))
            
            # Track responses and check for issues
            agent_responses = []
            issues_found = []
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('status') == 'done':
                        agent = data.get('agent', 'unknown')
                        content = data.get('content', '')
                        agent_responses.append({'agent': agent, 'content': content})
                        
                        print(f"✅ {agent.upper()} response:")
                        print(f"   💬 {content}")
                        
                        # Check for self-labeling issues
                        content_lower = content.lower()
                        
                        # Check for explicit self-identification
                        self_labels = [f"{agent}:", f"{agent} here", f"as {agent}", f"i am {agent}"]
                        found_labels = [label for label in self_labels if label in content_lower]
                        
                        if found_labels:
                            issues_found.append(f"{agent}: Self-labeling found - {found_labels}")
                            print(f"   ❌ ISSUE: Self-labeling detected: {found_labels}")
                        else:
                            print(f"   ✅ No self-labeling detected")
                        
                        # Check for third-person references
                        third_person = [f"the {agent}", f"{agent} thinks", f"{agent} believes"]
                        found_third_person = [ref for ref in third_person if ref in content_lower]
                        
                        if found_third_person:
                            issues_found.append(f"{agent}: Third-person reference - {found_third_person}")
                            print(f"   ❌ ISSUE: Third-person detected: {found_third_person}")
                        else:
                            print(f"   ✅ Proper first-person usage")
                        
                        # Check for multi-persona confusion
                        other_agents = [a for a in ['catalyst', 'anchor', 'weaver'] if a != agent]
                        mixed_personas = [other for other in other_agents if other in content_lower]
                        
                        if mixed_personas:
                            issues_found.append(f"{agent}: Mixed personas - {mixed_personas}")
                            print(f"   ❌ ISSUE: Multiple personas in response: {mixed_personas}")
                        else:
                            print(f"   ✅ Single persona maintained")
                        
                        print()
                        
                    elif data.get('status') == 'awaiting_user':
                        print("🎯 TESTING COMPLETE")
                        print(f"📊 FINAL ASSESSMENT:")
                        print(f"   💬 Total responses tested: {len(agent_responses)}")
                        
                        if not issues_found:
                            print(f"   ✅ SUCCESS: No self-labeling issues detected!")
                            print(f"   🎉 All agents responded naturally without self-identification")
                        else:
                            print(f"   ❌ ISSUES FOUND: {len(issues_found)}")
                            for issue in issues_found:
                                print(f"      - {issue}")
                        
                        break
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"❌ Error: {e}")
                    continue
            
    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure FastAPI is running:")
        print("   cd app && uvicorn main:app --reload --host 127.0.0.1 --port 8000")
    except Exception as e:
        print(f"❌ Test failed: {e}")

async def test_concise_discussion():
    uri = "ws://127.0.0.1:8000/ws-chat"
    
    print("🚀 Testing Concise Multi-Turn Discussions")
    print(f"📍 Connecting to: {uri}")
    print("=" * 70)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Test with custom autonomous rounds
            test_message = {
                "message": "Should we prioritize AI safety or innovation speed?",
                "temperature": 0.7,
                "autonomous_rounds": 3  # Test with 3 rounds
            }
            
            print(f"📤 Sending: {test_message['message']}")
            print(f"⚙️  Autonomous rounds: {test_message['autonomous_rounds']}")
            print("\n🎭 CONCISE CONVERSATION FLOW:")
            print("=" * 50)
            
            await websocket.send(json.dumps(test_message))
            
            # Track conversation metrics
            message_count = 0
            agent_responses = {agent: [] for agent in ["catalyst", "anchor", "weaver"]}
            started_autonomous = False
            response_lengths = []
            
            start_time = time.time()
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_count += 1
                    
                    agent = data.get('agent', 'unknown')
                    content = data.get('content', '')
                    status = data.get('status')
                    
                    # Handle different message types
                    if status == 'typing':
                        print(f"💭 {agent.upper()} thinking...")
                        
                    elif status == 'done':
                        # Track response quality
                        if agent in agent_responses:
                            agent_responses[agent].append(content)
                            response_num = len(agent_responses[agent])
                            
                            # Check response length (should be concise)
                            word_count = len(content.split())
                            response_lengths.append(word_count)
                            
                            # Determine if this is autonomous discussion
                            total_responses = sum(len(responses) for responses in agent_responses.values())
                            if total_responses > 3 and not started_autonomous:
                                print("\n🤖 AUTONOMOUS DISCUSSION:")
                                print("-" * 30)
                                started_autonomous = True
                            
                            phase = "INITIAL" if response_num == 1 and not started_autonomous else "AUTO"
                            
                            print(f"✅ {agent.upper()} ({phase} #{response_num}) [{word_count} words]:")
                            print(f"   💬 {content}")
                            
                            # Check for conciseness (should be 1-2 sentences)
                            sentence_count = content.count('.') + content.count('!') + content.count('?')
                            if sentence_count <= 2:
                                print(f"   ✅ Concise ({sentence_count} sentences)")
                            else:
                                print(f"   ⚠️  Verbose ({sentence_count} sentences)")
                            
                            # Check for forbidden elements
                            forbidden_elements = ['*', 'i agree', 'great idea', 'as catalyst', 'as anchor', 'as weaver']
                            found_forbidden = [elem for elem in forbidden_elements if elem in content.lower()]
                            if found_forbidden:
                                print(f"   ❌ Found forbidden elements: {found_forbidden}")
                            else:
                                print(f"   ✅ Clean, direct response")
                            
                            print()
                        
                    elif status == 'awaiting_user':
                        duration = time.time() - start_time
                        print("🎯 DISCUSSION CONCLUDED")
                        print(f"⏸️  {data.get('message', 'Agents are waiting for user input')}")
                        print(f"⏱️  Discussion time: {duration:.1f} seconds")
                        
                        # Response analysis
                        total_responses = sum(len(responses) for responses in agent_responses.values())
                        avg_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
                        
                        print(f"\n📊 CONCISENESS ANALYSIS:")
                        print(f"   💬 Total responses: {total_responses}")
                        print(f"   📏 Average response length: {avg_length:.1f} words")
                        print(f"   🎯 Target: ≤30 words per response")
                        
                        if avg_length <= 30:
                            print(f"   ✅ Excellent conciseness!")
                        elif avg_length <= 50:
                            print(f"   ⚡ Good conciseness")
                        else:
                            print(f"   ❌ Too verbose - needs improvement")
                        
                        for agent, responses in agent_responses.items():
                            print(f"   {agent.capitalize()}: {len(responses)} responses")
                        
                        print("\n✅ Concise discussion test completed!")
                        break
                        
                    elif not status:  # User message
                        if agent == 'user':
                            print(f"👤 USER:")
                            print(f"   💬 {content}")
                            print("\n🎬 INITIAL RESPONSES:")
                            print("-" * 30)
                    
                    # Safety timeout
                    if message_count >= 30:
                        print("⏰ Test timeout - moving on...")
                        break
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"❌ Error: {e}")
                    continue
            
    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure FastAPI is running:")
        print("   cd app && uvicorn main:app --reload --host 127.0.0.1 --port 8000")
    except Exception as e:
        print(f"❌ Test failed: {e}")

async def test_different_round_counts():
    """Test different autonomous round settings"""
    uri = "ws://127.0.0.1:8000/ws-chat"
    
    print("\n" + "="*70)
    print("🔢 TESTING DIFFERENT ROUND COUNTS")
    print("="*70)
    
    test_rounds = [2, 4, 6]
    
    for rounds in test_rounds:
        print(f"\n🔸 Testing {rounds} autonomous rounds")
        
        try:
            async with websockets.connect(uri) as websocket:
                test_message = {
                    "message": f"Test message for {rounds} rounds of discussion.",
                    "temperature": 0.7,
                    "autonomous_rounds": rounds
                }
                
                await websocket.send(json.dumps(test_message))
                
                response_count = 0
                start_time = time.time()
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        if data.get('status') == 'done':
                            response_count += 1
                            
                        elif data.get('status') == 'awaiting_user':
                            duration = time.time() - start_time
                            print(f"   ✅ {rounds} rounds completed: {response_count} responses in {duration:.1f}s")
                            break
                            
                    except json.JSONDecodeError:
                        continue
                    except asyncio.TimeoutError:
                        print(f"   ⏰ Timeout for {rounds} rounds")
                        break
                
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"   ❌ Failed testing {rounds} rounds: {e}")
    
    print("\n✅ Round count testing completed!")

async def test_response_quality():
    """Test for natural, concise responses without forbidden elements"""
    uri = "ws://127.0.0.1:8000/ws-chat"
    
    print("\n" + "="*70)
    print("🎭 TESTING RESPONSE QUALITY")
    print("="*70)
    
    try:
        async with websockets.connect(uri) as websocket:
            test_message = {
                "message": "What's the best approach to climate change?",
                "temperature": 0.8,
                "autonomous_rounds": 3
            }
            
            print(f"📤 Testing response quality with: {test_message['message']}")
            print("\n📝 QUALITY CHECKS:")
            
            await websocket.send(json.dumps(test_message))
            
            responses = []
            quality_score = 0
            total_checks = 0
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('status') == 'done':
                        content = data.get('content', '').lower()
                        responses.append(content)
                        
                        # Quality checks
                        total_checks += 4  # 4 checks per response
                        
                        # 1. No asterisks or stage directions
                        if '*' not in content:
                            quality_score += 1
                            print(f"   ✅ No asterisks/stage directions")
                        else:
                            print(f"   ❌ Contains asterisks: {content}")
                        
                        # 2. No repetitive acknowledgments
                        repetitive = ['i agree', 'great idea', 'good point', 'exactly right']
                        if not any(phrase in content for phrase in repetitive):
                            quality_score += 1
                            print(f"   ✅ No repetitive acknowledgments")
                        else:
                            found = [phrase for phrase in repetitive if phrase in content]
                            print(f"   ❌ Repetitive phrases: {found}")
                        
                        # 3. No role announcements
                        role_announces = ['as catalyst', 'as anchor', 'as weaver']
                        if not any(announce in content for announce in role_announces):
                            quality_score += 1
                            print(f"   ✅ No role announcements")
                        else:
                            print(f"   ❌ Contains role announcements")
                        
                        # 4. Reasonable length (concise)
                        word_count = len(content.split())
                        if word_count <= 35:
                            quality_score += 1
                            print(f"   ✅ Concise ({word_count} words)")
                        else:
                            print(f"   ⚠️  Verbose ({word_count} words)")
                        
                        print()
                        
                    elif data.get('status') == 'awaiting_user':
                        break
                        
                except json.JSONDecodeError:
                    continue
            
            # Final quality assessment
            quality_percentage = (quality_score / total_checks) * 100 if total_checks > 0 else 0
            
            print(f"📊 FINAL QUALITY SCORE:")
            print(f"   🎯 Quality: {quality_score}/{total_checks} ({quality_percentage:.1f}%)")
            print(f"   💬 Total responses analyzed: {len(responses)}")
            
            if quality_percentage >= 90:
                print("   ✅ Excellent quality!")
            elif quality_percentage >= 75:
                print("   ⚡ Good quality")
            else:
                print("   ❌ Needs improvement")
                
    except Exception as e:
        print(f"❌ Quality test failed: {e}")

if __name__ == "__main__":
    print("🧪 RUNNING IMPROVED HIVE DISCUSSION TESTS...\n")
    asyncio.run(test_no_self_labeling())  # NEW: Test the specific self-labeling fix
    asyncio.run(test_concise_discussion())
    asyncio.run(test_different_round_counts())
    asyncio.run(test_response_quality()) 