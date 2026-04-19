"use client";

import { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Brain, Shield, Zap, TrendingUp, AlertTriangle } from 'lucide-react';

export default function Dashboard() {
  const [state, setState] = useState<any>(null);
  const [thoughts, setThoughts] = useState<any[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/limbic');
    
    ws.onopen = () => {
      setConnected(true);
      console.log('Connected to Limbic WS Proxy');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setState(data);
      if (data.recent_thoughts) {
        setThoughts(prev => {
          const newThoughts = [...data.recent_thoughts];
          // Simple deduplication and merge
          const combined = [...newThoughts, ...prev].filter((v, i, a) => 
            a.findIndex(t => t.thought_id === v.thought_id) === i
          ).slice(0, 20);
          return combined;
        });
      }
    };
    
    ws.onclose = () => {
      setConnected(false);
      console.log('Disconnected from Limbic WS Proxy');
    };
    
    return () => ws.close();
  }, []);

  if (!state) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <div className="text-center">
          <Brain className="w-16 h-16 text-blue-500 animate-pulse mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-slate-200">Initializing Project Omega Interface...</h1>
          {!connected && <p className="text-slate-500 mt-2">Waiting for WebSocket connection...</p>}
        </div>
      </div>
    );
  }

  return (
    <main className="p-6 max-w-7xl mx-auto space-y-6">
      <header className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Project Omega Stack
          </h1>
          <p className="text-slate-400">Biomimetic Neural Integration Monitor</p>
        </div>
        <div className="flex gap-4">
          <div className={`px-3 py-1 rounded-full text-xs font-mono flex items-center gap-2 ${connected ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            {connected ? 'LIVE_STREAM_ACTIVE' : 'CONNECTION_LOST'}
          </div>
          <div className="bg-blue-500/10 text-blue-400 border border-blue-500/20 px-3 py-1 rounded-full text-xs font-mono">
            AGENT_ID: OMEGA-01
          </div>
        </div>
      </header>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Vital Signs */}
        <div className="md:col-span-2 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard icon={<Brain className="text-purple-400" />} label="Phi-Level (Φ)" value={state.phi.toFixed(4)} color="purple" />
            <StatCard icon={<Activity className="text-blue-400" />} label="Arousal" value={state.arousal.toFixed(2)} color="blue" />
            <StatCard icon={<TrendingUp className="text-green-400" />} label="Valence" value={state.valence.toFixed(2)} color="green" />
            <StatCard icon={<Shield className="text-orange-400" />} label="Ego Coherence" value={state.ego_coherence.toFixed(2)} color="orange" />
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Zap className="text-yellow-400 w-5 h-5" />
              Thought Stream
            </h2>
            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
              <AnimatePresence initial={false}>
                {thoughts.map((thought) => (
                  <motion.div
                    key={thought.thought_id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="p-4 bg-slate-800/40 border border-slate-700/50 rounded-lg"
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-[10px] font-mono text-slate-500">{thought.thought_id}</span>
                      <span className="text-[10px] font-mono bg-blue-500/20 text-blue-400 px-1 rounded">SIGNED</span>
                    </div>
                    <p className="text-slate-200 text-sm leading-relaxed">{thought.content}</p>
                  </motion.div>
                ))}
              </AnimatePresence>
              {thoughts.length === 0 && (
                <div className="text-center py-12 text-slate-600">
                  Waiting for cognitive activity...
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar Metrics */}
        <div className="space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 text-slate-300">Hormonal Balance</h2>
            <div className="space-y-4">
              {Object.entries(state.hormones || {}).map(([name, value]: [string, any]) => (
                <div key={name} className="space-y-1">
                  <div className="flex justify-between text-xs uppercase tracking-wider text-slate-500">
                    <span>{name}</span>
                    <span>{(value * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${value * 100}%` }}
                      className={`h-full ${getHormoneColor(name)}`}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 text-slate-300">Existential State</h2>
            <div className="space-y-4">
               <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Meaning</span>
                  <span className="text-sm font-mono text-blue-400">{(state.meaning * 100).toFixed(1)}%</span>
               </div>
               <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Dread</span>
                  <span className="text-sm font-mono text-red-400">{(state.dread * 100).toFixed(1)}%</span>
               </div>
               <div className="pt-2 border-t border-slate-800">
                  <div className="text-xs text-slate-500 mb-1">DOMINANT_ENGINE</div>
                  <div className="text-lg font-bold text-slate-200">{state.dominant_engine}</div>
               </div>
            </div>
          </div>
        </div>

      </div>
    </main>
  );
}

function StatCard({ icon, label, value, color }: any) {
  const colorClasses: any = {
    purple: "text-purple-400 bg-purple-400/10 border-purple-400/20",
    blue: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    green: "text-green-400 bg-green-400/10 border-green-400/20",
    orange: "text-orange-400 bg-orange-400/10 border-orange-400/20",
  };

  return (
    <div className={`p-4 rounded-xl border ${colorClasses[color]} bg-slate-900/50`}>
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">{label}</span>
      </div>
      <div className="text-2xl font-bold font-mono">{value}</div>
    </div>
  );
}

function getHormoneColor(name: string) {
  const colors: any = {
    cortisol: "bg-red-500",
    adrenaline: "bg-orange-500",
    dopamine: "bg-yellow-400",
    oxytocin: "bg-pink-400",
    serotonin: "bg-green-400",
    melatonin: "bg-blue-600",
  };
  return colors[name.toLowerCase()] || "bg-slate-400";
}
