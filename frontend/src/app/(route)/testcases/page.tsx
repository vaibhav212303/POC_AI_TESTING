"use client";

import { useState, useEffect, useCallback } from "react";
import { 
  Plus, Trash2, Save, Play, FileJson, 
  Globe, MousePointer2, Type, Eye,
  Sparkles, Undo2, Redo2, Loader2
} from "lucide-react";

// --- Types ---
type StepAction = "navigate" | "click" | "fill" | "check" | "wait" | "press";

interface TestStep {
  id: string;
  action: StepAction;
  selector?: string;
  value?: string;
  description?: string;
}

interface TestCase {
  title: string;
  description: string;
  baseUrl: string;
  steps: TestStep[];
}

export default function TestCaseView() {
  // --- State ---
  const [testCase, setTestCase] = useState<TestCase>({
    title: "", description: "", baseUrl: "",
    steps: [{ id: "1", action: "navigate", value: "", description: "Open Base URL" }]
  });

  // History State
  const [history, setHistory] = useState<TestCase[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // AI State
  const [aiPrompt, setAiPrompt] = useState("");
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"builder" | "preview">("builder");

  // --- History Management ---
  const addToHistory = useCallback((newState: TestCase) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(JSON.parse(JSON.stringify(newState))); // Deep copy
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [history, historyIndex]);

  // Initial History
  useEffect(() => {
    if (history.length === 0) addToHistory(testCase);
  }, []);

  const handleUndo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setTestCase(history[historyIndex - 1]);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setTestCase(history[historyIndex + 1]);
    }
  };

  const updateTestCase = (newState: TestCase) => {
    setTestCase(newState);
    addToHistory(newState);
  };

  // --- AI Generation ---
  const handleAiGenerate = async () => {
    if (!aiPrompt.trim()) return;
    setIsAiLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/generate-steps", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: aiPrompt, provider: "gemini" }) // Configurable provider
      });
      
      const data = await res.json();
      
      if (data.steps) {
        // Append generated steps to current steps
        const newSteps = [...testCase.steps, ...data.steps];
        updateTestCase({ ...testCase, steps: newSteps });
        setAiPrompt("");
      } else {
        alert("AI Failed: " + JSON.stringify(data));
      }
    } catch (e) {
      alert("Error connecting to AI Backend");
    } finally {
      setIsAiLoading(false);
    }
  };

  // --- Handlers ---
  const addStep = () => {
    const newStep: TestStep = {
      id: Math.random().toString(36).substr(2, 9),
      action: "click", selector: "", value: "", description: ""
    };
    updateTestCase({ ...testCase, steps: [...testCase.steps, newStep] });
  };

  const removeStep = (id: string) => {
    if (testCase.steps.length === 1) return;
    updateTestCase({ ...testCase, steps: testCase.steps.filter(s => s.id !== id) });
  };

  const updateStep = (id: string, field: keyof TestStep, value: string) => {
    const newSteps = testCase.steps.map(s => s.id === id ? { ...s, [field]: value } : s);
    // Don't add every keystroke to history, purely local state update
    setTestCase({ ...testCase, steps: newSteps });
  };
  
  // Save to History on Blur (Wait until user finishes typing)
  const handleBlur = () => {
    addToHistory(testCase);
  };

  const handleSaveFile = async () => {
    const filename = (testCase.title.replace(/\s+/g, "_").toLowerCase() || "untitled") + ".json";
    const res = await fetch("http://localhost:8000/api/save-testcase", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename, content: testCase })
    });
    const data = await res.json();
    if(data.status === "success") alert(`Saved to ${data.path}`);
    else alert("Save failed");
  };

  return (
    <div className="flex flex-col h-full bg-[#09090b] text-zinc-100">
      
      {/* HEADER */}
      <header className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-[#09090b]">
        <div className="flex items-center gap-4">
          <h1 className="font-semibold tracking-tight text-sm">Test Builder</h1>
          <div className="h-4 w-[1px] bg-white/10" />
          <div className="flex gap-1 bg-zinc-900 p-0.5 rounded-lg border border-white/5">
            <button onClick={() => setActiveTab("builder")} className={`px-3 py-1 text-[10px] uppercase font-bold rounded-md transition-all ${activeTab === "builder" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-500 hover:text-zinc-300"}`}>Builder</button>
            <button onClick={() => setActiveTab("preview")} className={`px-3 py-1 text-[10px] uppercase font-bold rounded-md transition-all ${activeTab === "preview" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-500 hover:text-zinc-300"}`}>JSON</button>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button onClick={handleUndo} disabled={historyIndex <= 0} className="p-2 hover:bg-zinc-800 rounded disabled:opacity-30"><Undo2 className="w-4 h-4" /></button>
          <button onClick={handleRedo} disabled={historyIndex >= history.length - 1} className="p-2 hover:bg-zinc-800 rounded disabled:opacity-30"><Redo2 className="w-4 h-4" /></button>
          <div className="h-4 w-[1px] bg-white/10 mx-2" />
          <button onClick={handleSaveFile} className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-md transition-colors"><Save className="w-3.5 h-3.5" /> Save</button>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          
          {activeTab === "builder" ? (
            <>
              {/* METADATA & AI GENERATOR */}
              <div className="bg-zinc-900/50 border border-white/5 rounded-xl p-5 space-y-5">
                
                {/* AI BAR */}
                <div className="relative group">
                  <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-lg opacity-20 group-hover:opacity-40 transition duration-500 blur"></div>
                  <div className="relative flex items-center bg-zinc-950 rounded-lg border border-white/10 px-3 py-2 gap-3">
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    <input 
                      className="flex-1 bg-transparent border-none text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none"
                      placeholder="Ask AI: 'Login with standard_user and check inventory'..."
                      value={aiPrompt}
                      onChange={(e) => setAiPrompt(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleAiGenerate()}
                      disabled={isAiLoading}
                    />
                    <button 
                      onClick={handleAiGenerate}
                      disabled={!aiPrompt || isAiLoading}
                      className="text-xs bg-white text-black px-3 py-1.5 rounded font-medium hover:bg-zinc-200 disabled:opacity-50 flex items-center gap-2"
                    >
                      {isAiLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : "Generate Steps"}
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] font-bold text-zinc-500 uppercase">Test Title</label>
                    <input 
                      className="w-full bg-transparent border-b border-zinc-700 py-1 text-sm focus:border-indigo-500 outline-none transition-colors"
                      placeholder="E.g., Valid User Login"
                      value={testCase.title}
                      onChange={(e) => setTestCase({...testCase, title: e.target.value})}
                      onBlur={handleBlur}
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-zinc-500 uppercase">Base URL</label>
                    <input 
                      className="w-full bg-transparent border-b border-zinc-700 py-1 text-sm focus:border-indigo-500 outline-none transition-colors font-mono text-zinc-400"
                      placeholder="https://..."
                      value={testCase.baseUrl}
                      onChange={(e) => setTestCase({...testCase, baseUrl: e.target.value})}
                      onBlur={handleBlur}
                    />
                  </div>
                </div>
              </div>

              {/* STEPS */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-zinc-500 px-1">
                  <span>EXECUTION STEPS</span>
                  <span>{testCase.steps.length} Steps</span>
                </div>

                {testCase.steps.map((step, index) => (
                  <div key={step.id} className="flex gap-3 items-start bg-zinc-900/30 border border-white/5 rounded-lg p-3 hover:border-white/10 transition-colors group">
                    <div className="w-6 h-6 rounded bg-zinc-800 flex items-center justify-center text-xs font-mono text-zinc-500 mt-0.5">
                      {index + 1}
                    </div>

                    <div className="flex-1 grid grid-cols-12 gap-3">
                      <div className="col-span-2">
                        <select 
                          value={step.action}
                          onChange={(e) => updateStep(step.id, "action", e.target.value)}
                          onBlur={handleBlur}
                          className="w-full bg-zinc-950 border border-white/10 text-xs rounded px-2 py-1.5 outline-none focus:border-indigo-500"
                        >
                          <option value="navigate">Navigate</option>
                          <option value="click">Click</option>
                          <option value="fill">Fill</option>
                          <option value="check">Check</option>
                          <option value="wait">Wait</option>
                        </select>
                      </div>

                      <div className="col-span-4">
                        <input 
                          disabled={step.action === 'navigate' || step.action === 'wait'}
                          className="w-full bg-zinc-950 border border-white/10 rounded px-2 py-1.5 text-xs font-mono text-zinc-300 placeholder-zinc-700 outline-none focus:border-indigo-500 disabled:opacity-30"
                          placeholder="Selector (e.g. #id)"
                          value={step.selector}
                          onChange={(e) => updateStep(step.id, "selector", e.target.value)}
                          onBlur={handleBlur}
                        />
                      </div>

                      <div className="col-span-5">
                        <input 
                          className="w-full bg-zinc-950 border border-white/10 rounded px-2 py-1.5 text-xs text-zinc-300 placeholder-zinc-700 outline-none focus:border-indigo-500"
                          placeholder={step.action === 'navigate' ? 'URL' : 'Value / Expected'}
                          value={step.value}
                          onChange={(e) => updateStep(step.id, "value", e.target.value)}
                          onBlur={handleBlur}
                        />
                      </div>

                      <div className="col-span-1 flex justify-end">
                        <button onClick={() => removeStep(step.id)} className="p-1.5 text-zinc-600 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}

                <button 
                  onClick={addStep}
                  className="w-full py-2 border border-dashed border-white/10 rounded-lg text-zinc-600 text-xs font-medium hover:bg-white/5 hover:text-zinc-400 transition-all flex items-center justify-center gap-2"
                >
                  <Plus className="w-3.5 h-3.5" /> Add New Step
                </button>
              </div>
            </>
          ) : (
            <div className="bg-zinc-900 border border-white/10 rounded-xl overflow-hidden">
              <div className="p-4 overflow-x-auto">
                <pre className="text-xs font-mono text-emerald-400 leading-relaxed">
                  {JSON.stringify(testCase, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}