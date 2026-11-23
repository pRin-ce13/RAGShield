import React from 'react';
import { ShieldAlert, ShieldCheck, Activity, User, LogOut, Lock } from 'lucide-react';

export default function Navbar({ currentUser, backendOnline, onOpenAuth, onLogout }) {
  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center shadow-sm">
            <ShieldAlert className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-slate-900 tracking-tight">RAG<span className="text-blue-600">Shield</span></span>
              <span className="px-2 py-0.5 text-xs font-semibold rounded bg-slate-100 text-slate-700 border border-slate-200">
                v0.9.0
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">Automated Security Testing & Risk Assessment</p>
          </div>
        </div>

        {/* Backend Status & User Profile */}
        <div className="flex items-center space-x-4">
          
          {/* Live Backend Connection Indicator */}
          <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-xs">
            <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            <span className={backendOnline ? 'text-slate-700 font-medium' : 'text-red-600 font-medium'}>
              {backendOnline ? 'Backend Online (Port 8000)' : 'Backend Offline'}
            </span>
          </div>

          {/* User Account / Login */}
          {currentUser ? (
            <div className="flex items-center space-x-3 pl-2 border-l border-slate-200">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-semibold text-slate-900">{currentUser.full_name || currentUser.email}</p>
                <span className="text-[10px] uppercase font-bold tracking-wider text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                  {currentUser.role}
                </span>
              </div>
              <button
                onClick={onLogout}
                title="Log Out"
                className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition shadow-sm"
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
