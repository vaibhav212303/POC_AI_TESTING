'use client';

import { useEffect, useState } from "react";
import { getBuildHistory } from "@/lib/actions"; 
import { 
  CheckCircle2, XCircle, FileCode, Folder, Loader2, 
  Terminal, Hash, Monitor, Smartphone, Globe 
} from "lucide-react";

export default function AutomationDashboard() {
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

  const stats = selectedBuild?.results?.reduce((acc: any, spec: any) => {
    spec.tests.forEach((t: any) => {
      acc.total++;
      if (t.status === 'passed' || t.status === 'expected') acc.passed++;
    });
    return acc;
  }, { total: 0, passed: 0 }) || { total: 0, passed: 0 };

  if (loading) return (
    <div className="flex-1 flex items-center justify-center bg-[#09090b] h-screen">
      <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
    </div>
  );

  return (
    <div className="flex h-screen bg-[#09090b] text-zinc-300">
      {/* Sidebar */}
      <aside className="w-80 border-r border-white/5 overflow-y-auto bg-[#0b0b0d]">
        <div className="p-5 border-b border-white/5 bg-black/20 font-black text-[10px] uppercase tracking-[0.2em] text-zinc-500">
          Execution Builds
        </div>
        {builds.map((build) => (
          <button
            key={build.id}
            onClick={() => setSelectedBuild(build)}
            className={`w-full text-left p-5 border-b border-white/5 transition-all ${
              selectedBuild?.id === build.id ? 'bg-indigo-600/10 border-r-2 border-r-indigo-500' : 'hover:bg-white/5'
            }`}
          >
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-black text-white uppercase tracking-tight">Build #{build.id}</span>
              <StatusBadge status={build.status} />
            </div>
            <div className="flex items-center justify-between">
              <p className="text-[10px] text-zinc-500 font-mono">
                {new Date(build.createdAt).toLocaleDateString()} {new Date(build.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
              <span className="text-[9px] text-zinc-600 font-bold uppercase">{build.environment}</span>
            </div>
          </button>
        ))}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-10 bg-[#09090b]">
        <header className="mb-12">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
              <Hash className="w-6 h-6 text-indigo-500" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-white tracking-tight">Build #{selectedBuild?.id}</h1>
              <p className="text-zinc-500 text-sm font-medium">Platform: {selectedBuild?.results?.[0]?.specFile.includes('.cy.') ? 'Cypress' : 'Playwright'}</p>
            </div>
          </div>
          
          <div className="flex gap-3">
            <StatCard label="Tests" value={stats.total} color="text-indigo-400" />
            <StatCard label="Passed" value={stats.passed} color="text-green-400" />
            <StatCard label="Failed" value={stats.total - stats.passed} color="text-red-400" />
          </div>
        </header>

        <div className="space-y-10">
          {selectedBuild?.results?.map((spec: any) => (
            <div key={spec.id} className="group">
              {/* Spec File Label */}
              <div className="flex items-center gap-3 mb-4 px-2">
                <FileCode className="w-5 h-5 text-indigo-500/50" />
                <h2 className="text-md font-bold text-zinc-100 font-mono">{spec.specFile}</h2>
                <div className="h-px flex-1 bg-white/5 mx-4" />
                <span className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">{spec.tests.length} Executions</span>
              </div>

              <div className="bg-[#0c0c0e] border border-white/5 rounded-2xl p-6 shadow-2xl">
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
  const groupedBySuite = tests.reduce((acc: any, test: any) => {
    const suitePath = test.suites?.length > 0 ? test.suites.join("  ›  ") : "Root";
    if (!acc[suitePath]) acc[suitePath] = [];
    acc[suitePath].push(test);
    return acc;
  }, {});

  return (
    <div className="space-y-12">
      {Object.entries(groupedBySuite).map(([suitePath, suiteTests]: [string, any]) => {
        // Playwright logic: Detect browser from suite path
        const isChromium = suitePath.toLowerCase().includes('chromium');
        const isFirefox = suitePath.toLowerCase().includes('firefox');
        const isWebkit = suitePath.toLowerCase().includes('webkit');

        return (
          <div key={suitePath}>
            <div className="flex items-center gap-3 mb-6">
              <Folder className="w-4 h-4 text-zinc-600" />
              <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-zinc-400">
                {suitePath}
              </h3>
              {/* Browser Badges for Playwright */}
              {isChromium && <BrowserBadge name="Chromium" color="bg-blue-500/10 text-blue-400 border-blue-500/20" />}
              {isFirefox && <BrowserBadge name="Firefox" color="bg-orange-500/10 text-orange-400 border-orange-500/20" />}
              {isWebkit && <BrowserBadge name="Webkit" color="bg-pink-500/10 text-pink-400 border-pink-500/20" />}
            </div>

            <div className="ml-2 pl-8 border-l border-white/5 space-y-4">
              {suiteTests.map((test: any, idx: number) => (
                <div key={idx} className="group">
                  <div className="flex items-center justify-between py-2 px-3 rounded-xl hover:bg-white/[0.03] border border-transparent hover:border-white/5 transition-all">
                    <div className="flex items-center gap-4">
                      {test.status === 'passed' || test.status === 'expected' ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] font-black text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-md min-w-[50px] text-center">
                          {test.case_code || 'N/A'}
                        </span>
                        <span className="text-sm font-semibold text-zinc-300 group-hover:text-white transition-colors">
                          {test.title.replace(test.case_code || '', '').replace(/^[:\s-]+/, '').trim()}
                        </span>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono text-zinc-600">{test.duration}</span>
                  </div>

                  {test.status === 'failed' && (
                    <div className="mt-3 ml-12 p-4 bg-red-500/[0.03] border border-red-500/10 rounded-xl shadow-inner">
                      <div className="flex gap-3">
                        <Terminal className="w-4 h-4 text-red-500 shrink-0 mt-1" />
                        <code className="text-[11px] text-red-400/90 leading-relaxed font-mono whitespace-pre-wrap block">
                          {test.error}
                        </code>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function BrowserBadge({ name, color }: { name: string, color: string }) {
  return (
    <span className={`text-[8px] font-black uppercase px-2 py-0.5 rounded border ${color}`}>
      {name}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const isFailed = status === 'failed';
  return (
    <span className={`text-[9px] px-2 py-0.5 rounded-full font-black uppercase tracking-widest ${
      isFailed ? 'bg-red-500/10 text-red-500' : 'bg-green-500/10 text-green-500'
    }`}>
      {status}
    </span>
  );
}

function StatCard({ label, value, color }: { label: string, value: number, color: string }) {
  return (
    <div className="bg-[#111113] border border-white/5 px-6 py-3 rounded-2xl min-w-[120px]">
      <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500 mb-1">{label}</p>
      <p className={`text-2xl font-black ${color}`}>{value}</p>
    </div>
  );
}