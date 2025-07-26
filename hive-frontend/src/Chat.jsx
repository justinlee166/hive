import { useState, useEffect, useRef } from "react";

export default function Chat() {
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isWaitingForUser, setIsWaitingForUser] = useState(false);
  const [agentsDiscussing, setAgentsDiscussing] = useState(false);
  const [discussionRound, setDiscussionRound] = useState(0);
  const [autonomousRounds, setAutonomousRounds] = useState(4);
  const ws = useRef(null);
  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      
      if (isNearBottom) {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }
    }
  }, [history]);

  useEffect(() => {
    // Connect to FastAPI websocket
    const socket = new WebSocket("ws://127.0.0.1:8000/ws-chat");
    ws.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
      console.log("Connected to Hive backend");
    };

    socket.onclose = () => {
      setIsConnected(false);
      setIsWaitingForUser(false);
      setAgentsDiscussing(false);
      setDiscussionRound(0);
      console.log("Disconnected from Hive backend");
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      // Handle special awaiting_user status
      if (msg.status === "awaiting_user") {
        setIsWaitingForUser(true);
        setAgentsDiscussing(false);
        setDiscussionRound(0);
        
        // Add a system message to show agents are waiting
        const waitingMessage = {
          role: "system",
          agent: "system",
          content: msg.message || "Your turn! What's your take on this?",
          isWaiting: true
        };
        
        setHistory(prev => [...prev, waitingMessage]);
        return;
      }

      // Reset waiting state when agents start responding
      if (msg.status === "typing" || msg.role === "user") {
        setIsWaitingForUser(false);
        if (msg.status === "typing") {
          setAgentsDiscussing(true);
          // Estimate discussion round based on message count
          setDiscussionRound(prev => {
            const typingMsgs = history.filter(h => h.status === "typing").length;
            return Math.floor(typingMsgs / 3) + 1;
          });
        }
      }

      setHistory((prev) => {
        // Replace typing placeholder with final message when status is "done"
        if (msg.status === "done") {
          return prev.map((m) =>
            m.agent === msg.agent && m.status === "typing"
              ? { ...msg, status: undefined }
              : m
          );
        }
        // For "typing" or normal messages, just add to history
        return [...prev, msg];
      });
    };

    return () => {
      socket.close();
      setIsConnected(false);
      setIsWaitingForUser(false);
      setAgentsDiscussing(false);
      setDiscussionRound(0);
    };
  }, []);

  const send = () => {
    if (!input.trim() || !isConnected || (!isWaitingForUser && agentsDiscussing)) return;
    
    // Clear waiting state and system messages when user sends new message
    setIsWaitingForUser(false);
    setAgentsDiscussing(true);
    setDiscussionRound(1);
    setHistory(prev => prev.filter(msg => !msg.isWaiting));
    
    // Send message with autonomous rounds parameter
    ws.current.send(JSON.stringify({ 
      message: input, 
      temperature: 0.7,
      autonomous_rounds: autonomousRounds
    }));
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const resetChat = () => {
    setHistory([]);
    setIsWaitingForUser(false);
    setAgentsDiscussing(false);
    setDiscussionRound(0);
  };

  const getInputPlaceholder = () => {
    if (!isConnected) return "Connecting...";
    if (agentsDiscussing && !isWaitingForUser) return "Agents are discussing...";
    if (isWaitingForUser) return "Your turn! Share your thoughts...";
    return "Type your idea here...";
  };

  const getDiscussionStatus = () => {
    if (!agentsDiscussing || isWaitingForUser) return null;
    
    if (discussionRound <= 1) {
      return "Initial responses";
    } else {
      return `Round ${discussionRound - 1}/${autonomousRounds}`;
    }
  };

  const isInputDisabled = !isConnected || (agentsDiscussing && !isWaitingForUser);

  return (
    <div className="min-h-screen bg-white text-black">
      <div className="flex flex-col h-screen max-w-5xl mx-auto">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 shadow-sm px-6 py-4 sticky top-0 z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                } animate-pulse`}></div>
              </div>
              
              <div className="flex items-center gap-3">
                <span className="text-3xl">🐝</span>
                <h1 className="text-3xl font-bold text-gray-800">
                  Hive Collective
                </h1>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Enhanced Discussion Status */}
              {agentsDiscussing && !isWaitingForUser && (
                <div className="flex items-center gap-2 text-blue-600">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                  <span className="text-sm font-medium">
                    {getDiscussionStatus() || "Discussing..."}
                  </span>
                </div>
              )}
              
              {isWaitingForUser && (
                <div className="flex items-center gap-2 text-purple-600 animate-pulse">
                  <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                  <span className="text-sm font-medium">Your turn!</span>
                </div>
              )}
              
              <button
                onClick={resetChat}
                className="text-sm px-4 py-2 rounded-lg font-medium transition-colors bg-gray-100 hover:bg-gray-200 text-gray-700"
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* Controls Panel */}
        <div className="bg-white border-b border-gray-200 px-6 py-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex flex-col gap-3">
              {/* Inline Label with Value Display */}
              <div className="flex items-center gap-4">
                <label className="text-sm font-semibold text-gray-700">
                  Discussion Rounds:
                </label>
                <span className="text-lg font-bold text-blue-600">
                  {autonomousRounds}
                </span>
              </div>
              
              <div className="flex items-center gap-4">
                {/* Clean Slider */}
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium text-gray-500">2</span>
                  
                  <input
                    type="range"
                    min="2"
                    max="8"
                    value={autonomousRounds}
                    onChange={(e) => setAutonomousRounds(parseInt(e.target.value))}
                    disabled={agentsDiscussing && !isWaitingForUser}
                    className="w-32 h-2 bg-gray-200 rounded-full appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    style={{
                      background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((autonomousRounds - 2) / 6) * 100}%, #e5e7eb ${((autonomousRounds - 2) / 6) * 100}%, #e5e7eb 100%)`
                    }}
                  />
                  
                  <span className="text-xs font-medium text-gray-500">8</span>
                </div>
              </div>
            </div>
            
            <div className="text-xs text-gray-500 max-w-xs text-right">
              Agents will discuss for <strong>{autonomousRounds} rounds</strong> before asking for your input
            </div>
          </div>
        </div>

        {/* Chat Window - Plain Text */}
        <div 
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto px-6 py-4 space-y-4 bg-white"
        >
          {history.length === 0 && (
            <div className="text-center mt-20">
              <div className="text-8xl mb-6 animate-bounce">🐝</div>
              <h2 className="text-3xl font-bold mb-4 text-gray-800">Welcome to Hive!</h2>
              <p className="text-xl mb-4 text-gray-600">Start a conversation with our AI collective</p>
              <p className="text-sm max-w-lg mx-auto text-gray-500">
                Three distinct AI agents will engage in focused discussions before asking for your input
              </p>
            </div>
          )}
          
          {history.map((m, i) => {
            // Handle system/waiting messages
            if (m.role === "system" || m.isWaiting) {
              return (
                <div
                  key={i}
                  className="animate-fade-in-up text-center mb-4"
                >
                  <div className="inline-block px-4 py-2 bg-purple-100 border border-purple-200 text-purple-700 rounded-lg">
                    <div className="text-sm flex items-center justify-center gap-2">
                      <span>🎯</span>
                      <em className="font-medium">{m.content}</em>
                    </div>
                  </div>
                </div>
              );
            }
            
            const isUser = m.agent === "user";
            
            return (
              <div
                key={i}
                className="animate-fade-in-up mb-4"
              >
                <div className="max-w-4xl">
                  {/* Agent Name (for AI agents) */}
                  {!isUser && (
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">
                        {m.agent === 'catalyst' ? '🔥' : m.agent === 'anchor' ? '⚖️' : '🕸️'}
                      </span>
                      <span className="text-sm font-semibold text-gray-700">
                        {m.agent.charAt(0).toUpperCase() + m.agent.slice(1)}
                      </span>
                      {m.status === "typing" && (
                        <div className="flex space-x-1 ml-2">
                          <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce"></div>
                          <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* User Label (for user messages) */}
                  {isUser && (
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-semibold text-gray-700">You</span>
                      <span className="text-sm">👤</span>
                    </div>
                  )}
                  
                  {/* Plain Text Message */}
                  <div className="text-base leading-relaxed text-black">
                    {m.status === "typing" ? (
                      <div className="flex items-center gap-2 text-gray-600">
                        <span>💭</span>
                        <em>thinking...</em>
                      </div>
                    ) : (
                      <span className="whitespace-pre-wrap">{m.content}</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
          
          {/* Auto-scroll anchor */}
          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 px-6 py-4 shadow-lg">
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <textarea
                className={`w-full border-2 rounded-lg p-4 focus:outline-none focus:ring-2 transition-all resize-none ${
                  isWaitingForUser 
                    ? "focus:ring-purple-500 border-purple-300 bg-purple-50" 
                    : "focus:ring-blue-500 border-gray-300 bg-white"
                } shadow-sm`}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={getInputPlaceholder()}
                disabled={isInputDisabled}
                rows={1}
                style={{ minHeight: '56px', maxHeight: '120px' }}
              />
            </div>
            <button
              className={`px-6 py-4 rounded-lg font-semibold transition-all duration-200 shadow-lg ${
                isConnected && input.trim() && (isWaitingForUser || !agentsDiscussing)
                  ? isWaitingForUser
                    ? "bg-purple-500 hover:bg-purple-600 text-white"
                    : "bg-blue-500 hover:bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-500 cursor-not-allowed"
              }`}
              onClick={send}
              disabled={isInputDisabled || !input.trim()}
            >
              {isWaitingForUser ? "Continue" : "Send"}
            </button>
          </div>
          
          {/* Agent Info */}
          <div className="mt-4 text-xs text-center text-gray-500">
            <span className="font-medium">AI Agents:</span>
            <span className="text-orange-600 ml-2">🔥 Catalyst (Visionary)</span>
            <span className="text-green-600 ml-1">• ⚖️ Anchor (Practical)</span>
            <span className="text-blue-600 ml-1">• 🕸️ Weaver (Synthesizer)</span>
          </div>
          
          {/* Dynamic Help text */}
          {agentsDiscussing && !isWaitingForUser && (
            <div className="mt-3 text-xs text-center text-blue-600 animate-pulse">
              Agents are having a focused {autonomousRounds}-round discussion. They'll ask for your input when ready!
            </div>
          )}
          
          {isWaitingForUser && (
            <div className="mt-3 text-xs text-center font-medium text-purple-600 animate-pulse">
              The agents have concluded their discussion. Share your perspective to continue!
            </div>
          )}
        </div>
      </div>

      {/* Basic CSS for animations */}
      <style jsx>{`
        @keyframes fade-in-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in-up {
          animation: fade-in-up 0.4s ease-out;
        }
        
        /* Basic Slider Styling */
        input[type="range"]::-webkit-slider-thumb {
          appearance: none;
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }
        
        input[type="range"]::-moz-range-thumb {
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }
      `}</style>
    </div>
  );
}
