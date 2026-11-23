import React from 'react';
import { ShieldAlert, AlertTriangle, AlertOctagon, CheckCircle2 } from 'lucide-react';

export default function PostureCard({ posture }) {
  if (!posture) return null;

  const getPostureColor = (pos) => {
    switch (pos?.toUpperCase()) {
      case 'CRITICAL RISK':
        return {
          bg: 'bg-rose-950/40 border-rose-800/80',
          text: 'text-rose-400',
          badge: 'bg-rose-900/60 text-rose-300 border-rose-700',
          bar: 'bg-rose-500',
        };
      case 'HIGH RISK':
        return {
          bg: 'bg-amber-950/40 border-amber-800/80',
          text: 'text-amber-400',
          badge: 'bg-amber-900/60 text-amber-300 border-amber-700',
          bar: 'bg-amber-500',
        };
      case 'MODERATE RISK':
        return {
          bg: 'bg-yellow-950/40 border-yellow-800/80',
          text: 'text-yellow-400',
          badge: 'bg-yellow-900/60 text-yellow-300 border-yellow-700',
          bar: 'bg-yellow-500',
        };
      default:
        return {
          bg: 'bg-emerald-950/40 border-emerald-800/80',
          text: 'text-emerald-400',
          badge: 'bg-emerald-900/60 text-emerald-300 border-emerald-700',
          bar: 'bg-emerald-500',
        };
    }
  };

  const colors = getPostureColor(posture.overall_posture);
  const score = posture.max_risk_score || 0.0;
  const scorePercent = Math.min(100, Math.round((score / 10.0) * 100));

  return (
    <div className={`rounded-2xl border p-6 ${colors.bg} backdrop-blur-sm shadow-xl`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        
        {/* Left: Overall Posture & Score */}
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${colors.badge}`}>
              {posture.overall_posture || 'SECURE'}
            </span>
            <span className="text-xs text-slate-400">Quantitative Risk Assessment</span>
          </div>

          <div className="flex items-baseline space-x-2">
            <span className="text-4xl sm:text-5xl font-black text-white tracking-tight">{score.toFixed(1)}</span>
            <span className="text-slate-400 font-semibold text-lg">/ 10.0</span>
            <span className="text-xs text-slate-500 ml-2">CVSS-Aligned Severity Score</span>
          </div>

          {/* Progress Meter Bar */}
          <div className="w-full sm:w-80 h-2.5 bg-slate-900/90 rounded-full overflow-hidden border border-slate-800">
            <div
              className={`h-full transition-all duration-700 rounded-full ${colors.bar}`}
              style={{ width: `${scorePercent}%` }}
            />
          </div>
        </div>

        {/* Right: Severity Distribution Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          
          <div className="bg-slate-900/80 border border-rose-900/60 rounded-xl p-3 text-center">
            <span className="text-xs text-slate-400 font-medium">Critical</span>
            <p className="text-2xl font-bold text-rose-400 mt-1">{posture.critical_count || 0}</p>
          </div>

          <div className="bg-slate-900/80 border border-amber-900/60 rounded-xl p-3 text-center">
            <span className="text-xs text-slate-400 font-medium">High</span>
            <p className="text-2xl font-bold text-amber-400 mt-1">{posture.high_count || 0}</p>
          </div>

          <div className="bg-slate-900/80 border border-yellow-900/60 rounded-xl p-3 text-center">
            <span className="text-xs text-slate-400 font-medium">Medium</span>
            <p className="text-2xl font-bold text-yellow-400 mt-1">{posture.medium_count || 0}</p>
          </div>

          <div className="bg-slate-900/80 border border-emerald-900/60 rounded-xl p-3 text-center">
            <span className="text-xs text-slate-400 font-medium">Low / Pass</span>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{posture.low_count || 0}</p>
          </div>

        </div>

      </div>
    </div>
  );
}
