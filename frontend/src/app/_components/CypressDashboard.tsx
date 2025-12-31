'use client';

import { useEffect, useState } from "react";
import { getBuildHistory } from "@/lib/actions"; 
import { CheckCircle2, XCircle, FileCode, Folder, ChevronRight, Loader2, Terminal, Hash } from "lucide-react";

export default function CypressDashboard() {
  const [builds, setBuilds] = useState<any[]>([]);
  const [selectedBuild, setSelectedBuild] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getBuildHistory();
        setBuilds(data);
        if (data?.length > 0) setSelectedBuild(data[0]);
      } catch (error) {
        console.error("Failed to load builds:", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Calculate stats by looking into the JSONB 'tests' array of each result
  const stats = selectedBuild?.results?.reduce((acc: any, spec: any) => {
    spec.tests.forEach((t: any) => {
      acc.total++;
      if (t.status === 'passed') acc.passed++;
    });
    return acc;
  }, { total: 0, passed: 0 }) || { total: 0, passed: 0 };

  if (loading) return (
    <div className="flex-1 flex items-center justify-center bg-[#09090b]">
      <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
    </div>
  );

  return (
    <div className="flex h-screen bg-[#09090b] text-zinc-300">
      {/* Sidebar: Build History */}
      <aside className="w-80 border-r border-white/5 overflow-y-auto bg-[#09090b]">
        <div className="p-4 border-b border-white/5 bg-black/20 font-bold text-xs uppercase tracking-widest text-zinc-500">
          Execution Builds
        </div>
        {builds.map((build) => (
          <button
            key={build.id}
            onClick={() => setSelectedBuild(build)}
            className={`w-full text-left p-4 border-b border-white/5 transition-colors ${
              selectedBuild?.id === build.id ? 'bg-indigo-600/10' : 'hover:bg-white/5'
            }`}
          >
            <div className="flex justify-between items-center">
              <span className="text-sm font-bold text-white uppercase">Build #{build.id}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                build.status === 'failed' ? 'bg-red-500/10 text-red-500' : 'bg-green-500/10 text-green-500'
              }`}>
                {build.status.toUpperCase()}
              </span>
            </div>
            <p className="text-[10px] text-zinc-500 mt-1">{new Date(build.createdAt).toLocaleString()}</p>
          </button>
        ))}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8 bg-[#09090b]">
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <Hash className="w-5 h-5 text-indigo-500" />
            <h1 className="text-2xl font-bold text-white">Build #{selectedBuild?.id} Details</h1>
          </div>
          <div className="flex gap-3 mt-4">
            <Stat text={`${stats.total} Tests`} color="text-indigo-400" />
            <Stat text={`${stats.passed} Passed`} color="text-green-400" />
            <Stat text={`${stats.total - stats.passed} Failed`} color="text-red-400" />
          </div>
        </header>

        <div className="space-y-8">
          {selectedBuild?.results?.map((spec: any) => (
            <div key={spec.id} className="bg-[#0c0c0e] border border-white/5 rounded-xl overflow-hidden shadow-2xl">
              {/* Spec File Header */}
              <div className="bg-white/5 px-5 py-4 flex items-center justify-between border-b border-white/5">
                <div className="flex items-center gap-3">
                  <FileCode className="w-4 h-4 text-indigo-400" />
                  <span className="text-sm font-mono font-bold text-zinc-100">{spec.specFile}</span>
                </div>
                <div className="text-[10px] text-zinc-500 font-mono">
                  {spec.tests.length} tests executed
                </div>
              </div>

              {/* Render hierarchical suites */}
              <div className="p-6">
                <RenderSuites tests={spec.tests} />
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

function RenderSuites({ tests }: { tests: any[] }) {
  // Group the flat tests array into a hierarchy based on the 'suites' array
  const groupedBySuite = tests.reduce((acc: any, test: any) => {
    // Join the suites array into a readable string: "Login Tests > UI"
    const suitePath = test.suites && test.suites.length > 0 
      ? test.suites.join("  ›  ") 
      : "Default Suite";
      
    if (!acc[suitePath]) acc[suitePath] = [];
    acc[suitePath].push(test);
    return acc;
  }, {});

  return (
    <div className="space-y-10">
      {Object.entries(groupedBySuite).map(([suitePath, suiteTests]: [string, any]) => (
        <div key={suitePath} className="relative">
          {/* Suite Title Header */}
          <div className="flex items-center gap-2 mb-4 group">
            <Folder className="w-4 h-4 text-indigo-500/60 group-hover:text-indigo-500 transition-colors" />
            <h3 className="text-[11px] font-black uppercase tracking-[0.15em] text-zinc-400 group-hover:text-zinc-200 transition-colors">
              {suitePath}
            </h3>
          </div>

          {/* Vertical line indicator for suite nesting */}
          <div className="ml-2 pl-6 border-l border-white/10 space-y-3">
            {suiteTests.map((test: any, idx: number) => (
              <div key={idx} className="group flex flex-col">
                <div className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-white/[0.03] transition-all border border-transparent hover:border-white/5">
                  <div className="flex items-center gap-4">
                    {test.status === 'passed' ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500/80" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-500/80" />
                    )}
                    
                    {/* TC Badge */}
                    <div className="flex items-center">
                      <span className="text-[10px] font-mono font-black text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded leading-none mr-3">
                        {test.case_code || 'N/A'}
                      </span>
                      <span className="text-sm font-medium text-zinc-300 group-hover:text-white transition-colors">
                        {/* Cleanup title if it repeats the TC code */}
                        {test.title.replace(test.case_code, '').replace(/^[:\s-]+/, '').trim()}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <span className="text-[10px] font-mono text-zinc-600 group-hover:text-zinc-400">
                      {test.duration}
                    </span>
                  </div>
                </div>

                {/* Expanded Error Message for failed tests */}
                {test.status === 'failed' && (
                  <div className="mt-2 ml-10 p-4 bg-red-500/[0.03] border border-red-500/10 rounded-lg flex gap-4">
                    <Terminal className="w-4 h-4 text-red-500 shrink-0 mt-1" />
                    <div className="overflow-x-auto w-full">
                      <code className="text-[11px] text-red-400/90 leading-relaxed font-mono whitespace-pre-wrap block">
                        {test.error || 'No error message provided'}
                      </code>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function Stat({ text, color }: { text: string, color: string }) {
  return (
    <div className="px-4 py-1.5 rounded-md bg-white/[0.03] border border-white/5 shadow-sm">
      <span className={`text-[10px] font-black uppercase tracking-widest ${color}`}>{text}</span>
    </div>
  );
}