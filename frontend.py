import { useState, useEffect, useRef } from "react";

type Msg = { role:string; agent:string; content:string|null; status?:string; };

export default function Chat() {
  const [history, setHistory] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const ws = useRef<WebSocket|null>(null);

  useEffect(() => {
    ws.current = new WebSocket("ws://127.0.0.1:8000/ws-chat");
    ws.current.onmessage = e => {
      const msg: Msg = JSON.parse(e.data);
      setHistory(h => {
        // Replace typing placeholder or append
        if (msg.status === "done") {
          return h.map(m =>
            m.agent === msg.agent && m.status === "typing"
              ? { role: msg.role, agent: msg.agent, content: msg.content! }
              : m
          );
        } else {
          return [...h, msg];
        }
      });
    };
    return () => ws.current?.close();
  }, []);

  const send = () => {
    if (!ws.current || !input.trim()) return;
    ws.current.send(JSON.stringify({message: input, temperature:0.7}));
    setInput("");
  };

  return (
    <div>
      <div className="chat-window">
        {history.map((m,i) => (
          <div key={i} className={`bubble ${m.agent}`}>
            <b>{m.agent}:</b>{" "}
            {m.status === "typing" ? <em>…typing</em> : m.content}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={e=>setInput(e.target.value)}
        onKeyDown={e=>e.key==="Enter" && send()}
      />
      <button onClick={send}>Send</button>
    </div>
  );
}
