"use client";

import { useState, useEffect, useRef } from "react";

type Message = { role: "user" | "ai"; content: string; image?: string };
type Log = { text: string; timestamp: string };

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [logs, setLogs] = useState<Log[]>([]);
  const [input, setInput] = useState("");
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [status, setStatus] = useState("Disconnected");
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Config State
  const [provider, setProvider] = useState("gemini");
  const [model, setModel] = useState("models/gemini-1.5-flash");

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Connect to Python Backend
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => setStatus("Connected 🟢");
    ws.onclose = () => setStatus("Disconnected 🔴");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "log") {
        setLogs((prev) => [...prev, { text: data.content, timestamp: new Date().toLocaleTimeString() }]);
      } 
      else if (data.type === "response") {
        setMessages((prev) => [...prev, { role: "ai", content: data.content }]);
        setIsProcessing(false);
      } 
      else if (data.type === "image") {
        // Add image as a specialized AI message
        setMessages((prev) => [...prev, { role: "ai", content: "📸 Screenshot captured:", image: data.content }]);
      }
      else if (data.type === "done") {
        setIsProcessing(false);
      }
    };

    setSocket(ws);
    return () => ws.close();
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, logs]);

  const sendMessage = () => {
    if (!input || !socket) return;

    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setIsProcessing(true);
    
    // Send to Backend
    socket.send(JSON.stringify({ 
      message: input,
      config: { provider, model }
    }));
    
    setInput("");
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white font-sans">
      
      {/* SIDEBAR: Config & Logs */}
      <div className="w-1/3 border-r border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-700 bg-gray-800">
          <h1 className="text-xl font-bold mb-2">🤖 QA Architect</h1>
          <div className="text-sm mb-4">Status: {status}</div>
          
          {/* Settings */}
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400">Provider</label>
              <select 
                className="w-full bg-gray-700 p-2 rounded mt-1"
                value={provider} onChange={(e) => setProvider(e.target.value)}
              >
                <option value="gemini">Gemini</option>
                <option value="groq">Groq</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400">Model ID</label>
              <input 
                className="w-full bg-gray-700 p-2 rounded mt-1"
                value={model} onChange={(e) => setModel(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Live Logs */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-black font-mono text-xs">
          <div className="text-gray-500 sticky top-0 bg-black pb-2 border-b border-gray-800">EXECUTION LOGS</div>
          {logs.map((log, i) => (
            <div key={i} className="text-green-400 break-words">
              <span className="text-gray-500">[{log.timestamp}]</span> {log.text}
            </div>
          ))}
          <div ref={scrollRef} />
        </div>
      </div>

      {/* MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-2xl p-4 rounded-lg ${msg.role === "user" ? "bg-blue-600" : "bg-gray-800 border border-gray-700"}`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.image && (
                  <img 
                    src={`data:image/png;base64,${msg.image}`} 
                    className="mt-3 rounded border border-gray-600 shadow-lg"
                    alt="Screenshot" 
                  />
                )}
              </div>
            </div>
          ))}
          {isProcessing && <div className="text-gray-500 p-4 animate-pulse">Thinking & Executing...</div>}
        </div>

        {/* INPUT BAR */}
        <div className="p-4 border-t border-gray-700 bg-gray-800">
          <div className="flex gap-2">
            <input
              className="flex-1 bg-gray-900 border border-gray-600 rounded p-3 text-white focus:outline-none focus:border-blue-500"
              placeholder="Navigate to saucedemo.com..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button 
              onClick={sendMessage}
              disabled={isProcessing}
              className="bg-blue-600 hover:bg-blue-700 px-6 rounded font-semibold disabled:opacity-50"
            >
              Run
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}