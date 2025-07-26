# Concise Hive Chat Test Plan

## Overview
This test plan verifies the refined concise multi-turn discussion features with parameterized autonomous rounds in the Hive chat system.

## Key Features to Test

### 1. Concise Multi-Turn Discussions
- **Expected**: Agents engage in brief, focused responses (1-2 sentences, ≤30 words)
- **Behavior**: Direct, action-oriented conversation without repetitive acknowledgments
- **Rounds**: User-configurable (2-8 rounds) via frontend slider

### 2. Natural Conversation Style
- **No stage directions**: Eliminated ALL `*asterisks*` and meta-commentary
- **No repetitive politeness**: Removed "I agree", "great idea", etc. at start of turns
- **No role announcements**: Eliminated "As Catalyst" or agent self-identification
- **Direct communication**: Forward-looking, action-oriented responses

### 3. Parameterized Discussion Length
- **Slider control**: Frontend slider (2-8 rounds) controls discussion length
- **Backend parameter**: `autonomous_rounds` sent with user message
- **Dynamic stopping**: Discussion concludes after specified rounds
- **Clear feedback**: "Your turn!" message when agents pause

### 4. Maintained Personality Differences
- **Catalyst**: Bold, visionary, proposes next moves directly
- **Anchor**: Practical, questions feasibility, offers concrete steps
- **Weaver**: Synthesizer, bridges perspectives concisely

## Test Procedures

### Phase 1: Backend Testing

#### Start the Backend
```bash
cd app
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

#### Run Concise Discussion Tests
```bash
python test_websocket.py
```

**Expected Output:**
```
🚀 Testing Concise Multi-Turn Discussions
✅ Connected successfully!
📤 Sending: Should we prioritize AI safety or innovation speed?
⚙️  Autonomous rounds: 3

🎭 CONCISE CONVERSATION FLOW:
==================================================
👤 USER:
   💬 Should we prioritize AI safety or innovation speed?

🎬 INITIAL RESPONSES:
------------------------------
💭 CATALYST thinking...
✅ CATALYST (INITIAL #1) [18 words]:
   💬 Speed drives breakthroughs that save lives. Excessive caution kills innovation potential.
   ✅ Concise (2 sentences)
   ✅ Clean, direct response

🤖 AUTONOMOUS DISCUSSION:
------------------------------
💭 ANCHOR thinking...
✅ ANCHOR (AUTO #2) [22 words]:
   💬 But rushed AI deployment without safety protocols could cause catastrophic failures. We need minimum viable safeguards.
   ✅ Concise (2 sentences)
   ✅ Clean, direct response

🎯 DISCUSSION CONCLUDED
⏸️  Your turn! What's your take on this?

📊 CONCISENESS ANALYSIS:
   💬 Total responses: 6-8
   📏 Average response length: 15-25 words
   🎯 Target: ≤30 words per response
   ✅ Excellent conciseness!
```

### Phase 2: Frontend Testing

#### Start the React Frontend
```bash
cd hive-frontend
npm run dev
```

#### Test in Browser (http://localhost:5173)

**Test Scenario 1: Slider Functionality**
1. **Adjust slider** to 3 rounds
2. **Send**: "What's the future of work?"
3. **Observe**: Header shows "Round X/3" during discussion
4. **Verify**: Discussion stops after ~3 autonomous rounds
5. **Confirm**: Purple "Your turn!" appears with input re-enabled

**Test Scenario 2: Concise Response Quality**
1. **Set slider** to 5 rounds
2. **Send**: "Should we prioritize AI safety or innovation?"
3. **Check**: Each response is 1-2 sentences max
4. **Verify**: No asterisks, "I agree", or role announcements
5. **Observe**: Direct, action-oriented responses

**Test Scenario 3: Different Round Counts**
1. **Test 2 rounds**: Quick discussion, fast conclusion
2. **Test 6 rounds**: Extended discussion, more back-and-forth
3. **Test 8 rounds**: Maximum discussion length
4. **Verify**: UI correctly shows progress and conclusion

### Phase 3: Response Quality Assessment

#### Quality Indicators to Verify
✅ **Excellent indicators**:
- 1-2 sentences per response (≤30 words)
- Direct, action-oriented language
- No asterisks or stage directions
- No repetitive acknowledgments
- Forward-looking proposals
- Clear personality differences

❌ **Quality issues** (should be eliminated):
- Verbose responses (>35 words)
- Stage directions: `*nods*`, `*thinks*`
- Repetitive starts: "I agree", "Great idea"
- Role announcements: "As Catalyst"
- Meta-commentary about thinking styles

#### Sample Test Questions
1. "Climate change solutions?" (Should generate focused debate)
2. "AI safety vs innovation speed?" (Should create practical vs visionary tension)
3. "Future of remote work?" (Should generate synthesis and concrete steps)

## Success Criteria

### ✅ Backend Success Indicators
- [ ] Accepts `autonomous_rounds` parameter (2-8, default 4)
- [ ] Conducts exactly the specified number of autonomous rounds
- [ ] Responses average ≤30 words each
- [ ] Zero forbidden elements (asterisks, acknowledgments, role announcements)
- [ ] Sends `awaiting_user` status after discussion concludes
- [ ] Maintains distinct agent personalities in concise form

### ✅ Frontend Success Indicators  
- [ ] Slider controls autonomous rounds (2-8)
- [ ] Slider value sent with message to backend
- [ ] Progress indicator shows "Round X/Y" during discussion
- [ ] "Your turn!" appears when agents conclude
- [ ] Input disabled during discussion, enabled when agents pause
- [ ] Clear visual feedback for all states

### ✅ Conversation Quality Indicators
- [ ] 100% elimination of asterisks and stage directions
- [ ] 100% elimination of repetitive acknowledgments
- [ ] Average response length ≤30 words
- [ ] Clear personality differences maintained
- [ ] Forward-looking, action-oriented responses
- [ ] Natural conclusion with user input request

## Performance Targets

### Response Quality Metrics
- **Conciseness**: ≤30 words per response (target: 15-25 words)
- **Forbidden elements**: 0% (asterisks, acknowledgments, role announcements)
- **Sentence count**: 1-2 sentences per response
- **Quality score**: ≥90% on automated quality checks

### Timing Expectations
- **Initial responses**: 3 agents × ~1 second = ~3 seconds
- **Autonomous rounds**: N rounds × 3 agents × ~0.6 seconds = ~1.8N seconds
- **Total time**: 4-10 seconds depending on round setting
- **UI responsiveness**: Immediate feedback for all state changes

### Discussion Flow
- **Round progression**: Clear visual indication of progress
- **Natural conclusion**: Agents pause and request user input
- **User re-engagement**: Smooth transition back to user control
- **Context maintenance**: Agents build on previous responses without repetition

## Test Results Analysis

### Quality Assessment Rubric
- **Excellent (90-100%)**: Concise, direct, no forbidden elements
- **Good (75-89%)**: Mostly concise with minimal issues
- **Needs Improvement (<75%)**: Verbose or contains forbidden elements

### Automated Test Metrics
```bash
# Expected test output quality metrics:
📊 FINAL QUALITY SCORE:
   🎯 Quality: 24/24 (100.0%)
   💬 Total responses analyzed: 6
   ✅ Excellent quality!

🔢 TESTING DIFFERENT ROUND COUNTS
   ✅ 2 rounds completed: 8 responses in 4.2s
   ✅ 4 rounds completed: 14 responses in 7.8s  
   ✅ 6 rounds completed: 20 responses in 11.1s
```

## Troubleshooting

### Common Issues
1. **Verbose responses**: Check prompts include "IMPORTANT: Keep your response to 1-2 sentences maximum"
2. **Slider not working**: Verify `autonomous_rounds` parameter sent to backend
3. **No round indicator**: Check `discussionRound` state management in frontend
4. **Agents don't conclude**: Verify max_rounds logic in `conduct_concise_discussion`

### Debug Commands
```bash
# Backend logs with round tracking
cd app && uvicorn main:app --reload --log-level debug

# Test specific round count
python -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://127.0.0.1:8000/ws-chat') as ws:
        await ws.send(json.dumps({'message': 'test', 'autonomous_rounds': 3}))
        async for msg in ws:
            print(msg)
            if 'awaiting_user' in msg: break
asyncio.run(test())
"
```

## Success Metrics Summary
- **Conciseness**: 15-25 words per response average
- **Quality**: 100% elimination of forbidden elements  
- **Functionality**: Slider correctly controls discussion length
- **User Experience**: Clear progress indication and smooth transitions
- **Personality**: Distinct agent voices maintained in concise form
- **Technical**: Reliable WebSocket streaming with proper state management 