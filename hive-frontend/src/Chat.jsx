import { useState, useEffect, useRef } from "react";

const AGENT_COLORS = {
  catalyst: "bg-orange-200 border-orange-300",
  anchor: "bg-green-200 border-green-300", 
  weaver: "bg-blue-200 border-blue-300",
  user: "bg-gray-200 border-gray-300"
};

export default function Chat() {
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

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
      console.log("Disconnected from Hive backend");
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);

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
    };
  }, []);

  const send = () => {
    if (!input.trim() || !isConnected) return;
    ws.current.send(JSON.stringify({ message: input, temperature: 0.7 }));
    setInput("");
  };

  const resetChat = () => {
    setHistory([]);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-4">
          <h1 className="text-2xl font-bold text-center text-gray-800">
            Hive – Multi-Agent Collective
          </h1>
          <div className="flex justify-between items-center mt-2">
            <div className={`flex items-center gap-2 ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <button
              onClick={resetChat}
              className="text-sm bg-gray-500 text-white px-3 py-1 rounded hover:bg-gray-600"
            >
              Reset Chat
            </button>
          </div>
        </div>

        {/* Chat Window */}
        <div className="bg-white rounded-lg shadow-md h-[70vh] overflow-y-auto p-4 mb-4 space-y-3">
          {history.length === 0 && (
            <div className="text-center text-gray-500 mt-8">
              <p className="text-lg">Welcome to Hive!</p>
              <p className="text-sm">Start a conversation with our AI collective</p>
            </div>
          )}
          
          {history.map((m, i) => {
            const colorClass = AGENT_COLORS[m.agent] || "bg-gray-100 border-gray-200";
            
            return (
              <div
                key={i}
                className={`rounded-xl p-3 border-2 ${colorClass} ${
                  m.status === "typing" ? "opacity-70 animate-pulse" : ""
                }`}
              >
                <div className="font-semibold text-sm text-gray-700 mb-1">
                  {m.agent.charAt(0).toUpperCase() + m.agent.slice(1)}
                  {m.status === "typing" && " is thinking..."}
                </div>
                <div className="text-gray-800">
                  {m.status === "typing" ? (
                    <div className="flex items-center gap-1">
                      <span>💭</span>
                      <em className="text-gray-600">typing...</em>
                    </div>
                  ) : (
                    m.content
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Input Area */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex gap-2">
            <input
              className="flex-1 border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder={isConnected ? "Type a message..." : "Connecting..."}
              disabled={!isConnected}
            />
            <button
              className={`px-6 py-3 rounded-lg font-medium ${
                isConnected && input.trim()
                  ? "bg-blue-500 text-white hover:bg-blue-600"
                  : "bg-gray-300 text-gray-500 cursor-not-allowed"
              }`}
              onClick={send}
              disabled={!isConnected || !input.trim()}
            >
              Send
            </button>
          </div>
          
          {/* Agent Info */}
          <div className="mt-3 text-xs text-gray-500 text-center">
            <span className="font-medium">Agents:</span>
            <span className="text-orange-600 ml-1">Catalyst (Visionary)</span>
            <span className="text-green-600 ml-1">• Anchor (Practical)</span>
            <span className="text-blue-600 ml-1">• Weaver (Synthesizer)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
