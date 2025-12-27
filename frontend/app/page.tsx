'use client';

import { useState, useEffect, useRef } from 'react';
import { 
  Terminal, Play, Square, Trash2, 
  Cpu, Globe, ShieldCheck, AlertCircle, 
  CheckCircle2, ArrowRight, Sparkles, Server, Eye,
  Pause, PlayCircle, StepForward, Film, Download,
  Flame, Zap
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// --- UTILS ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- TYPES ---
type LogType = 'info' | 'thought' | 'action' | 'result' | 'error' | 'success' | 'bot' | 'done' | 'screenshot';
type ProviderType = 'ollama' | 'gemini' | 'grok' | 'groq';

interface LogEntry {
  type: LogType;
  content: string;
  timestamp: string;
}

// --- MAIN COMPONENT ---
export default function AgentDashboard() {
  // State
  const [task, setTask] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [liveImage, setLiveImage] = useState<string | null>(null);
  const [recordedVideoUrl, setRecordedVideoUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
  const [controlState, setControlState] = useState<'running' | 'paused'>('running');
  const [provider, setProvider] = useState<ProviderType>('groq'); // Default to Groq for speed
  
  // Refs
  const eventSourceRef = useRef<EventSource | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // --- HANDLERS ---

  const handleStart = () => {
    if (!task) return;
    
    // Reset state
    setLogs([]);
    setLiveImage(null);
    setRecordedVideoUrl(null);
    setStatus('running');
    setControlState('running');
    
    if (eventSourceRef.current) eventSourceRef.current.close();

    // Connect to Backend
    const BACKEND_URL = "https://automation-backend-9jov.onrender.com"; 
    const url = `${BACKEND_URL}/stream-task?task=${encodeURIComponent(task)}&model=${provider}`;
    
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // 1. Handle Live Video Frame
      if (data.type === 'video_frame') {
        setLiveImage(data.content);
        return; 
      }

      // 2. Handle Final Recording Download
      if (data.type === 'video_download') {
        setRecordedVideoUrl(data.content);
        return;
      }

      // 3. Handle Text Logs
      const newLog: LogEntry = {
        type: data.type,
        content: data.content,
        timestamp: new Date().toLocaleTimeString()
      };

      setLogs(prev => [...prev, newLog]);

      // 4. Handle Status Changes
      if (data.type === 'done') {
        setStatus('completed');
        es.close();
      } else if (data.type === 'error') {
        if(data.content.includes("Connection")) setStatus('error');
      }
    };

    es.onerror = () => {
      setLogs(prev => [...prev, {
        type: 'error', 
        content: 'Connection to Agent Brain lost.', 
        timestamp: new Date().toLocaleTimeString()
      }]);
      setStatus('error');
      es.close();
    };
  };

  const handleStop = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      setLogs(prev => [...prev, {
        type: 'info', 
        content: '🛑 Mission Aborted by User.', 
        timestamp: new Date().toLocaleTimeString()
      }]);
      setStatus('idle');
    }
  };

  const sendCommand = async (command: 'pause' | 'resume' | 'step') => {
    try {
      await fetch('https://automation-backend-9jov.onrender.com/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });
      
      if (command === 'pause') setControlState('paused');
      if (command === 'resume') setControlState('running');
      // Step acts as a temporary resume
    } catch (err) {
      console.error("Control failed", err);
    }
  };

  const clearLogs = () => {
    setLogs([]);
    setLiveImage(null);
    setRecordedVideoUrl(null);
    setStatus('idle');
  };

  // --- RENDER ---
  return (
    <div className="min-h-screen p-6 md:p-12 max-w-7xl mx-auto flex flex-col gap-6 bg-black text-white font-sans selection:bg-blue-500/30">
      
      {/* HEADER */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-gray-800 pb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-orange-500 bg-clip-text text-transparent flex items-center gap-3">
            <Cpu className="text-blue-500" />
            Autonomous Agent
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Multi-Model Web Automation Platform
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs font-mono bg-gray-900 px-3 py-1 rounded-full border border-gray-800 shadow-inner">
            <span className={cn("w-2 h-2 rounded-full animate-pulse", 
              status === 'running' ? "bg-green-500" : 
              status === 'error' ? "bg-red-500" : "bg-gray-500"
            )} />
            STATUS: {status.toUpperCase()}
          </div>
        </div>
      </header>

      {/* CONTROL PANEL */}
      <section className="bg-[#0a0a0a] border border-gray-800 rounded-xl p-3 shadow-2xl flex flex-col gap-3">
        
        {/* Model Selection Tabs */}
        <div className="flex gap-2 px-1 overflow-x-auto pb-2 scrollbar-hide">
          
          {/* GROQ (LPU) BUTTON */}
          <button 
            onClick={() => setProvider('groq')}
            disabled={status === 'running'}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all border whitespace-nowrap",
              provider === 'groq' 
                ? "bg-orange-950/40 border-orange-500/50 text-orange-400 shadow-[0_0_15px_rgba(249,115,22,0.15)]" 
                : "bg-gray-900/50 border-transparent text-gray-500 hover:text-gray-300 hover:bg-gray-800"
            )}
          >
            <Flame size={14} fill="currentColor" /> GROQ (Llama 3.3)
          </button>

          {/* GROK (xAI) BUTTON */}
          <button 
            onClick={() => setProvider('grok')}
            disabled={status === 'running'}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all border whitespace-nowrap",
              provider === 'grok' 
                ? "bg-gray-800 border-white/50 text-white shadow-[0_0_15px_rgba(255,255,255,0.15)]" 
                : "bg-gray-900/50 border-transparent text-gray-500 hover:text-gray-300 hover:bg-gray-800"
            )}
          >
            <Zap size={14} fill="currentColor" /> GROK (xAI)
          </button>
          
          {/* GEMINI BUTTON */}
          <button 
            onClick={() => setProvider('gemini')}
            disabled={status === 'running'}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all border whitespace-nowrap",
              provider === 'gemini' 
                ? "bg-purple-950/40 border-purple-500/50 text-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.15)]" 
                : "bg-gray-900/50 border-transparent text-gray-500 hover:text-gray-300 hover:bg-gray-800"
            )}
          >
            <Sparkles size={14} /> GEMINI
          </button>

          {/* OLLAMA BUTTON */}
          <button 
            onClick={() => setProvider('ollama')}
            disabled={status === 'running'}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all border whitespace-nowrap",
              provider === 'ollama' 
                ? "bg-blue-950/40 border-blue-500/50 text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.15)]" 
                : "bg-gray-900/50 border-transparent text-gray-500 hover:text-gray-300 hover:bg-gray-800"
            )}
          >
            <Server size={14} /> OLLAMA
          </button>
        </div>

        {/* Input Area */}
        <div className="flex flex-col md:flex-row gap-2">
          <div className="flex-1 relative group">
            <div className="absolute left-4 top-3.5 text-gray-600 group-focus-within:text-blue-500 transition-colors">
              <Terminal size={18} />
            </div>
            <input
              type="text"
              value={task}
              onChange={(e) => setTask(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && status !== 'running' && handleStart()}
              placeholder="Enter your mission (e.g., 'Go to google.com, search for data, and extract the table')"
              className="w-full bg-[#050505] border border-gray-800 text-gray-100 pl-12 pr-4 py-3 rounded-lg focus:ring-1 focus:ring-blue-900 focus:border-blue-800 outline-none transition-all font-mono text-sm placeholder:text-gray-700"
              disabled={status === 'running'}
            />
          </div>
          
          <div className="flex gap-2">
            {status === 'running' ? (
              <button 
                onClick={handleStop}
                className="bg-red-950/30 hover:bg-red-900/50 text-red-400 border border-red-900 px-6 py-2 rounded-lg font-medium transition-all flex items-center gap-2"
              >
                <Square size={16} fill="currentColor" /> Stop
              </button>
            ) : (
              <button 
                onClick={handleStart}
                disabled={!task}
                className="bg-blue-700 hover:bg-blue-600 text-white px-8 py-2 rounded-lg font-medium transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(37,99,235,0.2)] hover:shadow-[0_0_25px_rgba(37,99,235,0.4)]"
              >
                <Play size={18} fill="currentColor" /> Deploy
              </button>
            )}
            <button 
              onClick={clearLogs}
              className="bg-[#1a1a1a] hover:bg-[#252525] text-gray-400 px-3 rounded-lg border border-gray-800 transition-all"
              title="Clear Logs"
            >
              <Trash2 size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* --- LIVE PREVIEW WINDOW --- */}
      <section className="bg-black border border-gray-800 rounded-xl overflow-hidden shadow-2xl relative min-h-[300px] flex flex-col transition-all duration-500 group">
        <div className="bg-[#111] border-b border-gray-800 px-4 py-2 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${liveImage ? 'bg-red-500 animate-pulse' : 'bg-gray-600'}`} />
            <span className="text-xs text-gray-400 font-mono tracking-wider flex items-center gap-2">
              <Eye size={12} /> LIVE HEADLESS FEED
            </span>
          </div>
          <div className="flex gap-1.5 opacity-50">
            <div className="w-2 h-2 rounded-full bg-gray-600" />
            <div className="w-2 h-2 rounded-full bg-gray-600" />
            <div className="w-2 h-2 rounded-full bg-gray-600" />
          </div>
        </div>

        {/* MJPEG Stream Container */}
        <div className="flex-1 bg-[#050505] flex items-center justify-center p-4 relative">
          {liveImage ? (
            <img 
              src={`data:image/jpeg;base64,${liveImage}`} 
              alt="Live Browser Feed" 
              className="w-full max-h-[600px] object-contain rounded border border-gray-800 shadow-lg"
            />
          ) : (
            <div className="text-gray-700 flex flex-col items-center gap-3 py-10 opacity-30">
              <div className="w-24 h-16 border-2 border-gray-800 border-dashed rounded-lg flex items-center justify-center">
                <div className="w-2 h-2 bg-gray-800 rounded-full" />
              </div>
              <p className="text-xs font-mono">Waiting for video stream...</p>
            </div>
          )}
        </div>

        {/* FLOW CONTROL BAR */}
        <div className="bg-[#0f0f0f] border-t border-gray-800 p-3 flex justify-center gap-4">
            <button 
              onClick={() => sendCommand('resume')}
              disabled={status !== 'running' || controlState === 'running'}
              className="flex items-center gap-2 px-6 py-2 bg-green-950/20 text-green-400 border border-green-900/50 rounded hover:bg-green-900/40 disabled:opacity-30 disabled:cursor-not-allowed transition-all text-sm font-bold tracking-wide"
            >
              <PlayCircle size={16} /> RESUME
            </button>

            <button 
              onClick={() => sendCommand('pause')}
              disabled={status !== 'running' || controlState === 'paused'}
              className="flex items-center gap-2 px-6 py-2 bg-yellow-950/20 text-yellow-400 border border-yellow-900/50 rounded hover:bg-yellow-900/40 disabled:opacity-30 disabled:cursor-not-allowed transition-all text-sm font-bold tracking-wide"
            >
              <Pause size={16} /> PAUSE
            </button>

            <button 
              onClick={() => sendCommand('step')}
              disabled={status !== 'running' || controlState === 'running'}
              className="flex items-center gap-2 px-6 py-2 bg-blue-950/20 text-blue-400 border border-blue-900/50 rounded hover:bg-blue-900/40 disabled:opacity-30 disabled:cursor-not-allowed transition-all text-sm font-bold tracking-wide"
              title="Execute one step and pause again"
            >
              <StepForward size={16} /> STEP
            </button>
        </div>
      </section>

      {/* --- RECORDED SESSION PLAYER --- */}
      {recordedVideoUrl && (
        <section className="bg-[#050f05] border border-green-900/50 rounded-xl p-4 shadow-2xl animate-in fade-in slide-in-from-top-4">
          <div className="flex items-center justify-between mb-3 border-b border-green-900/30 pb-2">
            <div className="flex items-center gap-2 text-green-400 font-bold tracking-wider text-sm">
              <Film size={18} />
              SESSION RECORDING COMPLETE
            </div>
            <a 
              href={recordedVideoUrl} 
              download="agent-session.webm"
              className="inline-flex items-center gap-2 text-xs bg-green-900/20 text-green-400 px-3 py-1 rounded hover:bg-green-900/40 transition-colors"
            >
              <Download size={12} /> Download .webm
            </a>
          </div>
          <div className="aspect-video bg-black rounded overflow-hidden relative border border-green-900/30">
            <video 
              controls 
              autoPlay 
              className="w-full h-full object-contain"
              src={recordedVideoUrl}
            />
          </div>
        </section>
      )}

      {/* TERMINAL OUTPUT */}
      <main className="flex-1 bg-black border border-gray-800 rounded-xl overflow-hidden shadow-2xl flex flex-col min-h-[400px]">
        {/* Terminal Tab Bar */}
        <div className="bg-[#111] border-b border-gray-800 px-4 py-2 flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <div className="w-3 h-3 rounded-full bg-green-500/80" />
          </div>
          <span className="ml-4 text-xs text-gray-500 font-mono opacity-70">agent-stream.log</span>
        </div>

        {/* Logs Area */}
        <div className="flex-1 p-6 overflow-y-auto font-mono text-sm space-y-4">
          {logs.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-gray-700 gap-4 opacity-50">
              <Globe size={48} strokeWidth={1} />
              <p>System Online. Select a model and deploy agent...</p>
            </div>
          )}

          {logs.map((log, idx) => (
            <LogItem key={idx} log={log} />
          ))}
          
          <div ref={scrollRef} />
        </div>
      </main>
    </div>
  );
}

// --- SUB-COMPONENT: LOG ITEM RENDERING ---
function LogItem({ log }: { log: LogEntry }) {
  const styles = {
    info:    "text-gray-500 border-l-2 border-gray-700 pl-3",
    thought: "text-purple-400 italic pl-3 border-l-2 border-purple-900/50 bg-purple-900/5 p-2 rounded-r",
    action:  "text-orange-300 font-bold flex items-center gap-2 mt-4 mb-1",
    result:  "text-blue-300 pl-4 border-l border-blue-900/30 text-xs py-1",
    error:   "text-red-400 bg-red-950/30 border border-red-900/50 p-3 rounded my-2",
    success: "text-green-400 font-bold pl-3 border-l-2 border-green-700",
    bot:     "text-gray-100 bg-gray-900 border border-gray-800 p-4 rounded-lg my-4 shadow-lg",
    done:    "text-green-500 font-bold text-center py-4 border-t border-gray-800 mt-4",
    screenshot: "my-4", 
  };

  const icons = {
    action: <ArrowRight size={14} />,
    error: <AlertCircle size={16} />,
    success: <CheckCircle2 size={16} />,
    done: <ShieldCheck size={20} />,
  };

  if (log.type === 'bot') {
    return (
      <div className={styles.bot}>
        <div className="flex items-center gap-2 mb-2 text-indigo-400 text-xs uppercase tracking-wider font-bold">
          <Cpu size={14} /> Agent Response
        </div>
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{log.content}</ReactMarkdown>
        </div>
      </div>
    );
  }

  // --- SCREENSHOT RENDERER ---
  if (log.type === 'screenshot') {
    return (
      <div className="animate-in fade-in zoom-in duration-300 my-4 border border-gray-700 rounded-lg overflow-hidden bg-gray-900 max-w-2xl">
        <div className="bg-gray-800 px-3 py-1 text-xs text-gray-400 flex items-center gap-2 border-b border-gray-700">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          Verify Action Snapshot
        </div>
        <img 
          src={`data:image/png;base64,${log.content}`} 
          alt="Agent Screenshot" 
          className="w-full object-contain"
        />
      </div>
    );
  }

  return (
    <div className={cn("animate-in fade-in slide-in-from-bottom-1 duration-300", styles[log.type] || styles.info)}>
      {(log.type === 'action' || log.type === 'error' || log.type === 'success' || log.type === 'done') && (
        <span className="inline-block mr-2 align-text-bottom">
          {icons[log.type as keyof typeof icons]}
        </span>
      )}
      
      {['info', 'error', 'thought'].includes(log.type) && (
        <span className="text-[10px] text-gray-700 mr-2 uppercase tracking-widest">
          [{log.timestamp}]
        </span>
      )}

      <span className="break-words whitespace-pre-wrap">{log.content}</span>
    </div>
  );
}