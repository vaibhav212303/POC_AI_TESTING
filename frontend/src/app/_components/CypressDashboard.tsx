'use client';

import { useEffect, useState } from "react";
import { getBuildHistory } from "@/lib/actions"; // This is your Server Action
import { CheckCircle2, XCircle, Clock, Terminal, Loader2 } from "lucide-react";

export default function CypressDashboard() {
  const [builds, setBuilds] = useState<any[]>([]);
  const [selectedBuild, setSelectedBuild] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Fetch data on mount
  useEffect(() => {
    async function loadData() {
      try {
        const data = await getBuildHistory();
        setBuilds(data);
        if (data && data.length > 0) {
          setSelectedBuild(data[0]);
        }
      } catch (error) {
        console.error("Failed to load builds:", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#09090b]">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  if (builds.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#09090b] text-zinc-500">
        No execution builds found.
      </div>
    );
  }

  return (
    <div className="flex h-full bg-[#09090b] text-zinc-300">
      {/* Sidebar: Build List */}
      <aside className="w-80 border-r border-white/5 overflow-y-auto">
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
              <span className="text-sm font-bold text-white">BUILD #{build.id}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded ${
                build.status === 'failed' ? 'bg-red-500/10 text-red-500' : 'bg-green-500/10 text-green-500'
              }`}>
                {build.status.toUpperCase()}
              </span>
            </div>
            <p className="text-[10px] text-zinc-500 mt-1">
                {new Date(build.createdAt).toLocaleString()}
            </p>
          </button>
        ))}
      </aside>

      {/* Main Content: Test Details */}
      <main className="flex-1 p-8 overflow-y-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-white">Build #{selectedBuild?.id} Details</h1>
          <div className="flex gap-4 mt-2">
            <Stat text={`${selectedBuild?.results?.length || 0} Total Tests`} color="text-indigo-400" />
            <Stat text={`${selectedBuild?.results?.filter((r: any) => r.status === 'passed').length || 0} Passed`} color="text-green-400" />
          </div>
        </header>

        <div className="space-y-3">
          {selectedBuild?.results?.map((test: any) => (
            <div key={test.id} className="bg-[#111] border border-white/5 rounded-lg overflow-hidden">
              <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {test.status === 'passed' ? <CheckCircle2 className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-red-500" />}
                  <div>
                    <span className="text-[10px] font-mono text-indigo-500 font-bold">{test.caseCode}</span>
                    <h3 className="text-sm font-medium text-zinc-200">{test.title}</h3>
                  </div>
                </div>
                <span className="text-xs font-mono text-zinc-600">{test.duration}</span>
              </div>
              
              {test.status === 'failed' && (
                <div className="px-4 pb-4">
                  <div className="bg-black/40 p-3 rounded border border-red-500/10 flex gap-3">
                    <Terminal className="w-4 h-4 text-red-500 shrink-0 mt-1" />
                    <code className="text-[11px] text-red-400 leading-relaxed whitespace-pre-wrap">
                      {test.errorMessage}
                    </code>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

function Stat({ text, color }: { text: string, color: string }) {
  return <span className={`text-[11px] font-bold uppercase tracking-wider ${color}`}>{text}</span>;
}