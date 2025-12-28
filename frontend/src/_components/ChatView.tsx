"use client";

import { useState, useEffect, useRef } from "react";
import { 
  Bot, User, Send, Activity, 
  Terminal, CheckCircle2, XCircle, 
  ChevronRight, Command, Image as ImageIcon,
  MoreHorizontal
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

type Message = { role: "user" | "ai"; content: string; image?: string; timestamp: string };
type Log = { text: string; timestamp: string; type: "info" | "action" | "error" | "success" };

export default function ChatView() {
  // --- State ---
  const [messages, setMessages] = useState<Message[]>([]);
  const [logs, setLogs] = useState<Log[]>([]);
  const [input, setInput] = useState("");
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // --- Config ---
  const [provider, setProvider] = useState("groq");
  const [model, setModel] = useState("llama-3.3-70b-versatile");

  // --- Refs ---
  const logsEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // --- Connection ---
  useEffect(() => {
    // Establish independent socket for Chat Mode
    const ws = new WebSocket("ws://localhost:8000/ws");
    
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' });

      // Handle Logs
      if(data.type === "log") {
        let logType: Log["type"] = "info";
        if (data.content.includes("Action:")) logType = "action";
        else if (data.content.includes("Result:")) logType = "success";
        
        setLogs((prev) => [...prev, { text: data.content, timestamp: time, type: logType }]);
      } 
      // Handle Chat Response
      else if (data.type === "response") {
        setMessages((prev) => [...prev, { role: "ai", content: data.content, timestamp: time }]);
      } 
      // Handle Images
      else if (data.type === "image") {
        setMessages((prev) => [...prev, { role: "ai", content: "Screenshot Captured", image: data.content, timestamp: time }]);
      }
      // Handle Errors
      else if (data.type === "error") {
        setLogs((prev) => [...prev, { text: data.content, timestamp: time, type: "error" }]);
      }
      
      // Stop Processing State
      if(data.type === "done" || data.type === "response" || data.type === "error") {
        setIsProcessing(false);
      }
    };

    setSocket(ws);
    return () => ws.close();
  }, []);

  // --- Auto-Scroll ---
  useEffect(() => { logsEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [logs]);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isProcessing]);

  // --- Handlers ---
  const sendMessage = () => {
    if (!input.trim() || !socket || isProcessing) return;
    const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit' });
    setMessages((prev) => [...prev, { role: "user", content: input, timestamp: time }]);
    setIsProcessing(true);
    socket.send(JSON.stringify({ message: input, config: { provider, model } }));
    setInput("");
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => { 
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } 
  };

  return (
    <div className="flex h-full w-full bg-[#09090b]">
      
      {/* ================= CENTER PANEL: CHAT ================= */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* --- HEADER --- */}
        <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[#09090b]">
          <div className="flex items-center gap-4">
            <h2 className="font-medium text-white tracking-tight">Interactive Session</h2>
            <div className={cn("text-[10px] uppercase px-2 py-0.5 rounded-full border flex items-center gap-1.5 font-bold tracking-wider",
              isConnected ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-rose-500/10 text-rose-500 border-rose-500/20")}>
              {isConnected ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
              {isConnected ? "ONLINE" : "OFFLINE"}
            </div>
          </div>

          {/* Model Selector */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <select 
                value={provider} 
                onChange={e => setProvider(e.target.value)} 
                className="bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded-md pl-3 pr-8 py-1.5 outline-none focus:ring-1 focus:ring-indigo-500 appearance-none cursor-pointer hover:bg-zinc-800 transition-colors"
              >
                <option value="gemini">Gemini</option>
                <option value="groq">Groq</option>
                <option value="openai">OpenAI</option>
              </select>
              <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none">
                <ChevronRight className="w-3 h-3 text-zinc-500 rotate-90" />
              </div>
            </div>
            
            <input 
              value={model} 
              onChange={e => setModel(e.target.value)} 
              className="w-48 bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded-md px-3 py-1.5 outline-none focus:ring-1 focus:ring-indigo-500 placeholder:text-zinc-600"
              placeholder="Model ID"
            />
          </div>
        </header>
        
        {/* --- MESSAGES AREA --- */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-4 opacity-60">
              <div className="p-4 bg-zinc-900 rounded-full border border-zinc-800">
                <Command className="w-8 h-8" />
              </div>
              <p className="text-sm font-medium">Type a command to start automation...</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={cn("group flex items-start gap-4 max-w-3xl mx-auto", msg.role === "user" ? "flex-row-reverse" : "")}>
              <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border mt-0.5 shadow-sm", 
                msg.role === "user" ? "bg-indigo-600 border-indigo-500 text-white" : "bg-zinc-800 border-zinc-700 text-zinc-400")}>
                {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className={cn("flex flex-col gap-1 min-w-0 max-w-[80%]", msg.role === "user" ? "items-end" : "items-start")}>
                <div className="flex items-center gap-2 text-[10px] text-zinc-500 font-bold uppercase tracking-wider">
                  {msg.role === "user" ? "You" : "Agent"} <span className="opacity-50">• {msg.timestamp}</span>
                </div>
                
                {msg.content && (
                  <div className={cn("text-sm leading-relaxed px-4 py-3 rounded-xl border shadow-sm",
                    msg.role === "user" 
                      ? "bg-indigo-600/10 border-indigo-500/20 text-indigo-100" 
                      : "bg-zinc-900 border-zinc-800 text-zinc-300")}>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                )}
                
                {msg.image && (
                  <div className="mt-2 border border-white/10 rounded-lg overflow-hidden bg-black shadow-2xl relative group">
                    <img src={`data:image/png;base64,${msg.image}`} alt="Screenshot" className="w-full h-auto opacity-90 group-hover:opacity-100 transition-opacity" />
                  </div>
                )}
              </div>
            </div>
          ))}

          {isProcessing && (
            <div className="flex items-start gap-4 max-w-3xl mx-auto animate-pulse">
              <div className="w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-zinc-500" />
              </div>
              <div className="flex items-center gap-2 mt-2 text-zinc-500 text-xs font-medium uppercase tracking-wide">
                <Activity className="w-3 h-3 animate-spin" />
                <span>Executing Workflow...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* --- INPUT AREA --- */}
        <div className="p-6 pt-2 bg-gradient-to-t from-[#09090b] to-transparent">
          <div className="max-w-3xl mx-auto">
            <div className="relative flex items-center bg-zinc-900/80 backdrop-blur-xl p-1.5 rounded-xl border border-zinc-700/50 focus-within:border-indigo-500/50 focus-within:ring-1 focus-within:ring-indigo-500/20 transition-all shadow-lg">
              <input
                className="w-full bg-transparent text-sm text-zinc-100 placeholder-zinc-500 px-4 py-3 outline-none"
                placeholder="E.g., 'Go to google.com and search for AI agents'..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isProcessing}
                autoFocus
              />
              <button 
                onClick={sendMessage} 
                disabled={!input.trim() || isProcessing} 
                className="p-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg disabled:opacity-30 disabled:hover:bg-indigo-600 transition-all active:scale-95"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <div className="text-center mt-3 text-[10px] text-zinc-600 font-medium">
              Powered by Playwright & MCP • Press Enter to run
            </div>
          </div>
        </div>
      </div>

      {/* ================= RIGHT PANEL: ACTIVITY LOGS ================= */}
      <aside className="w-[400px] bg-[#0c0c0e] border-l border-white/5 flex flex-col hidden xl:flex">
        <div className="h-16 flex items-center justify-between px-5 border-b border-white/5 bg-[#09090b]/50">
          <div className="flex items-center gap-2 text-xs font-medium text-zinc-400 uppercase tracking-wider">
            <Terminal className="w-3.5 h-3.5" />
            <span>Execution Log</span>
          </div>
          <button className="text-zinc-600 hover:text-zinc-300 transition-colors">
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-[11px] scrollbar-thin scrollbar-thumb-zinc-800">
          {logs.length === 0 && <div className="text-zinc-700 mt-20 text-center italic">Waiting for events...</div>}
          
          {logs.map((log, i) => (
            <div key={i} className="flex gap-3 group animate-in fade-in slide-in-from-right-4 duration-300">
              <span className="text-zinc-600 shrink-0 select-none w-16 text-right">{log.timestamp}</span>
              
              <div className="flex flex-col gap-1 min-w-0 relative pl-3 border-l border-zinc-800">
                {/* Timeline Dot */}
                <div className={cn("absolute -left-[1.5px] top-1.5 w-[3px] h-[3px] rounded-full",
                  log.type === "action" ? "bg-blue-500" :
                  log.type === "success" ? "bg-emerald-500" :
                  log.type === "error" ? "bg-rose-500" : "bg-zinc-600"
                )} />

                <span className={cn("break-all leading-relaxed",
                  log.type === "action" ? "text-blue-300" :
                  log.type === "success" ? "text-emerald-300/80" :
                  log.type === "error" ? "text-rose-400" :
                  "text-zinc-500"
                )}>
                  {log.text}
                </span>
              </div>
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>
      </aside>

    </div>
  );
}