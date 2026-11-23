import React from 'react';
import { ShieldAlert, ShieldCheck, Activity, User, LogOut, Lock } from 'lucide-react';

export default function Navbar({ currentUser, backendOnline, onOpenAuth, onLogout }) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 p-0.5 flex items-center justify-center shadow-lg shadow-teal-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-teal-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">RAG<span className="text-teal-400">Shield</span></span>
              <span className="px-2 py-0.5 text-xs font-semibold rounded bg-teal-950/80 text-teal-400 border border-teal-800">
                v0.8.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Automated Security Testing & Risk Assessment</p>
          </div>
        </div>

        {/* Backend Status & User Profile */}
        <div className="flex items-center space-x-4">
          
          {/* Live Backend Connection Indicator */}
          <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-xs">
            <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className={backendOnline ? 'text-slate-300' : 'text-rose-400'}>
              {backendOnline ? 'Backend Online (Port 8000)' : 'Backend Offline'}
            </span>
          </div>

          {/* User Account / Login */}
          {currentUser ? (
            <div className="flex items-center space-x-3 pl-2 border-l border-slate-800">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-medium text-slate-200">{currentUser.full_name || currentUser.email}</p>
                <span className="text-[10px] uppercase font-semibold tracking-wider text-teal-400 bg-teal-950 px-1.5 py-0.5 rounded">
                  {currentUser.role}
                </span>
              </div>
              <button
                onClick={onLogout}
                title="Log Out"
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold transition shadow-md shadow-teal-500/10"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </button>
          )}

        </div>
      </div>
    </header>
  );
}
