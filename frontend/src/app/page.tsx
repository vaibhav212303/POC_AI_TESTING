"use client";

import { useState } from "react";
import {
  Bot,
  TestTube,
  FileCode,
  Bug,
  Settings,
  MessageSquare,
  PenTool,
  PlayCircle
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// --- Components ---
import ArchitectView from "@/app/_components/ArchitectView";
import ChatView from "@/app/_components/ChatView";
import CreateTestCase from "./(route)/testcases/page";
import CypressDashboard from "@/app/_components/CypressDashboard";
import AutomationDashboard from "./_components/PlaywrightDashboard";

function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

// Define view types
type ViewState = "chat" | "architect" | "testcases" | "cypress" | "playwright";

export default function Home() {
  const [activeView, setActiveView] = useState<ViewState>("chat");
  const [socket, setSocket] = useState<WebSocket | null>(null);

  // ... (WebSocket connection logic can stay here if needed globally)

  return (
    <div className="flex h-screen bg-[#111] text-zinc-300 font-sans text-sm antialiased">

      {/* SIDEBAR NAVIGATION */}
      <aside className="w-16 lg:w-64 bg-black/30 border-r border-white/5 flex flex-col transition-all duration-300">
        <div className="h-16 flex items-center justify-center lg:justify-start lg:px-6 gap-3 border-b border-white/5">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-900/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <h1 className="font-semibold text-white tracking-tighter hidden lg:block">QA Suite</h1>
        </div>

        <nav className="p-2 space-y-1 mt-4">
          <div className="px-3 pb-2 text-[10px] uppercase font-bold text-zinc-600 tracking-wider hidden lg:block">
            Automation
          </div>

          <NavItem
            icon={<MessageSquare className="w-4 h-4" />}
            label="AI Chat"
            isActive={activeView === "chat"}
            onClick={() => setActiveView("chat")}
          />

          <NavItem
            icon={<FileCode className="w-4 h-4" />}
            label="AI Architect"
            isActive={activeView === "architect"}
            onClick={() => setActiveView("architect")}
          />

          <NavItem
            icon={<PlayCircle className="w-4 h-4" />}
            label="Cypress Runner"
            isActive={activeView === "cypress"}
            onClick={() => setActiveView("cypress")}
          />
          <NavItem
            icon={<PlayCircle className="w-4 h-4" />}
            label="Playwright Runner"
            isActive={activeView === "playwright"}
            onClick={() => setActiveView("playwright")}
          />

          <div className="my-4 border-t border-white/5 mx-2" />

          <div className="px-3 pb-2 text-[10px] uppercase font-bold text-zinc-600 tracking-wider hidden lg:block">
            Manual
          </div>

          <NavItem
            icon={<PenTool className="w-4 h-4" />}
            label="Test Builder"
            isActive={activeView === "testcases"}
            onClick={() => setActiveView("testcases")}
          />

          <NavItem icon={<TestTube className="w-4 h-4" />} label="Test Runner" />
          <NavItem icon={<Bug className="w-4 h-4" />} label="Self-Healing" />
        </nav>

        <div className="mt-auto p-4 border-t border-white/5">
          <button className="flex items-center gap-3 p-2 rounded-md hover:bg-white/5 w-full text-zinc-500 hover:text-zinc-300 transition-colors">
            <Settings className="w-4 h-4" />
            <span className="hidden lg:block text-xs font-medium">Settings</span>
          </button>
        </div>
      </aside>

      {/* MAIN VIEW AREA */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#09090b]">
        {activeView === "chat" && <ChatView />}
        {activeView === "architect" && <ArchitectView socket={socket} />}
        {activeView === "testcases" && <CreateTestCase />}
        {activeView === "cypress" && <CypressDashboard />}
        {activeView === "playwright" && <AutomationDashboard />}
      </main>
    </div>
  );
}

// Helper Component for Sidebar Items
function NavItem({ icon, label, isActive, onClick }: any) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-md w-full transition-all group",
        isActive
          ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/20"
          : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
      )}
    >
      <span className={cn(isActive ? "text-indigo-400" : "text-zinc-500 group-hover:text-zinc-300")}>{icon}</span>
      <span className="hidden lg:block font-medium">{label}</span>
    </button>
  );
}