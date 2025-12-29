"use client";

import { useState, useRef, useEffect } from "react";
import { 
  Globe, Play, FileText, Code2, CheckCircle, 
  ArrowRight, Loader2, Save, Terminal, LayoutTemplate
} from "lucide-react";

type ArchitectStep = "input" | "planning" | "review" | "generating" | "complete";

interface ArchitectViewProps {
  socket: WebSocket | null;
}

export default function ArchitectView({ socket }: ArchitectViewProps) {
  const [step, setStep] = useState<ArchitectStep>("input");
  const [url, setUrl] = useState("");
  const [testPlan, setTestPlan] = useState("");
  const [logs, setLogs] = useState<string[]>([]);
  const [generatedFiles, setGeneratedFiles] = useState<{pom: string, spec: string} | null>(null);
  
  // Fake streaming simulation for UI demo (until backend is hooked up)
  const simulateDiscovery = () => {
    setStep("planning");
    addLog("Navigating to " + url + "...");
    addLog(" capturing screenshot...");
    addLog("Analyzing page structure (Gemini 1.5 Pro)...");
    
    setTimeout(() => {
      setTestPlan(`# Test Case: Login Flow
1. Navigate to ${url}
2. Locate username field (id: user-name)
3. Fill "standard_user"
4. Locate password field (id: password)
5. Fill "secret_sauce"
6. Click Login Button
7. Verify "Inventory" page is visible`);
      setStep("review");
    }, 2000);
  };

  const simulateGeneration = () => {
    setStep("generating");
    addLog("Generating Page Object Model...");
    addLog("Generating Test Spec...");
    addLog("Running Validator...");
    
    setTimeout(() => {
      setGeneratedFiles({
        pom: `export default class LoginPage {\n  // ... code ... \n}`,
        spec: `test('Login Flow', async ({ page }) => {\n  // ... code ... \n})`
      });
      setStep("complete");
    }, 2500);
  };

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  return (
    <div className="flex flex-col h-full bg-[#09090b] text-zinc-100">
      
      {/* --- STAGE HEADER --- */}
      <div className="h-16 border-b border-white/5 flex items-center px-8 justify-between bg-black/20">
        <div className="flex items-center gap-4 text-sm font-medium">
          <div className={`flex items-center gap-2 ${step === 'input' ? 'text-blue-400' : 'text-zinc-500'}`}>
            <div className="w-6 h-6 rounded-full border border-current flex items-center justify-center text-xs">1</div>
            Target
          </div>
          <div className="w-8 h-[1px] bg-zinc-800" />
          <div className={`flex items-center gap-2 ${['planning', 'review'].includes(step) ? 'text-blue-400' : 'text-zinc-500'}`}>
            <div className="w-6 h-6 rounded-full border border-current flex items-center justify-center text-xs">2</div>
            Strategy
          </div>
          <div className="w-8 h-[1px] bg-zinc-800" />
          <div className={`flex items-center gap-2 ${['generating', 'complete'].includes(step) ? 'text-blue-400' : 'text-zinc-500'}`}>
            <div className="w-6 h-6 rounded-full border border-current flex items-center justify-center text-xs">3</div>
            Code
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        
        {/* --- MAIN CONTENT AREA --- */}
        <div className="flex-1 p-8 overflow-y-auto">
          
          {/* STEP 1: INPUT */}
          {step === "input" && (
            <div className="max-w-2xl mx-auto mt-20 text-center space-y-8">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">What are we testing today?</h2>
                <p className="text-zinc-400">Enter a URL. The AI will scan it, devise a test plan, and write the automation code.</p>
              </div>
              
              <div className="flex items-center gap-2 bg-zinc-900/50 p-2 rounded-xl border border-white/10 shadow-xl">
                <div className="p-3 bg-zinc-800 rounded-lg">
                  <Globe className="w-5 h-5 text-zinc-400" />
                </div>
                <input 
                  className="flex-1 bg-transparent border-none outline-none text-zinc-100 placeholder-zinc-600 px-2"
                  placeholder="https://example.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                />
                <button 
                  onClick={simulateDiscovery}
                  disabled={!url}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Start Discovery <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 2: PLAN REVIEW */}
          {(step === "planning" || step === "review") && (
            <div className="max-w-4xl mx-auto h-full flex flex-col">
              {step === "planning" ? (
                <div className="flex flex-col items-center justify-center h-full space-y-4">
                  <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
                  <p className="text-zinc-400 animate-pulse">Analyzing page DOM & Visuals...</p>
                </div>
              ) : (
                <div className="flex flex-col h-full space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold flex items-center gap-2">
                        <FileText className="w-5 h-5 text-blue-400" /> Proposed Test Plan
                      </h3>
                      <p className="text-xs text-zinc-500">Edit the steps below to refine the AI's logic.</p>
                    </div>
                    <button 
                      onClick={simulateGeneration}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-md flex items-center gap-2"
                    >
                      <CheckCircle className="w-4 h-4" /> Approve & Generate
                    </button>
                  </div>
                  
                  <textarea 
                    value={testPlan}
                    onChange={(e) => setTestPlan(e.target.value)}
                    className="flex-1 bg-zinc-900/50 border border-white/10 rounded-xl p-6 font-mono text-sm text-zinc-300 focus:outline-none focus:ring-1 focus:ring-blue-500/50 resize-none leading-relaxed"
                  />
                </div>
              )}
            </div>
          )}

          {/* STEP 3: CODE GENERATION */}
          {(step === "generating" || step === "complete") && (
            <div className="max-w-6xl mx-auto h-full flex flex-col space-y-6">
              {step === "generating" ? (
                <div className="flex flex-col items-center justify-center h-64 space-y-4">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
                    <Code2 className="w-6 h-6 text-blue-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-zinc-400">Architecting Solution...</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-6 h-full">
                  {/* POM View */}
                  <div className="flex flex-col gap-2 min-h-0">
                    <div className="flex items-center justify-between px-1">
                      <span className="text-xs font-medium text-zinc-400 flex items-center gap-2">
                        <LayoutTemplate className="w-4 h-4" /> Page Object
                      </span>
                    </div>
                    <div className="flex-1 bg-zinc-900 border border-white/10 rounded-xl p-4 overflow-auto">
                      <pre className="text-xs font-mono text-blue-300">{generatedFiles?.pom}</pre>
                    </div>
                  </div>

                  {/* Spec View */}
                  <div className="flex flex-col gap-2 min-h-0">
                    <div className="flex items-center justify-between px-1">
                      <span className="text-xs font-medium text-zinc-400 flex items-center gap-2">
                        <Play className="w-4 h-4" /> Test Spec
                      </span>
                      <button className="text-xs bg-white text-black px-3 py-1 rounded-md font-medium hover:bg-zinc-200">
                        Run Test
                      </button>
                    </div>
                    <div className="flex-1 bg-zinc-900 border border-white/10 rounded-xl p-4 overflow-auto">
                      <pre className="text-xs font-mono text-emerald-300">{generatedFiles?.spec}</pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* --- RIGHT SIDEBAR: LIVE LOGS --- */}
        <div className="w-80 border-l border-white/5 bg-[#0c0c0e] flex flex-col">
          <div className="h-14 border-b border-white/5 flex items-center px-4 gap-2 text-xs font-medium text-zinc-400">
            <Terminal className="w-4 h-4" /> Architect Logs
          </div>
          <div className="flex-1 p-4 overflow-y-auto space-y-3 font-mono text-[11px] text-zinc-500">
            {logs.length === 0 && <span className="opacity-50">Waiting for start...</span>}
            {logs.map((log, i) => (
              <div key={i} className="break-words border-l-2 border-blue-500/30 pl-3">
                {log}
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}