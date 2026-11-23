import React from 'react';
import { ShieldAlert, AlertTriangle, AlertOctagon, CheckCircle2 } from 'lucide-react';

export default function PostureCard({ posture }) {
  if (!posture) return null;

  const getPostureColor = (pos) => {
    switch (pos?.toUpperCase()) {
      case 'CRITICAL RISK':
        return {
          cardBorder: 'border-red-200',
          badge: 'bg-red-100 text-red-800 border-red-200',
          bar: 'bg-red-600',
          scoreText: 'text-red-700',
        };
      case 'HIGH RISK':
        return {
          cardBorder: 'border-amber-200',
          badge: 'bg-amber-100 text-amber-800 border-amber-200',
          bar: 'bg-amber-600',
          scoreText: 'text-amber-700',
        };
      case 'MODERATE RISK':
        return {
          cardBorder: 'border-yellow-200',
          badge: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          bar: 'bg-yellow-500',
          scoreText: 'text-yellow-700',
        };
      default:
        return {
          cardBorder: 'border-emerald-200',
          badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
          bar: 'bg-emerald-600',
          scoreText: 'text-emerald-700',
        };
    }
  };

  const colors = getPostureColor(posture.overall_posture);
  const score = posture.max_risk_score || 0.0;
  const scorePercent = Math.min(100, Math.round((score / 10.0) * 100));

  return (
    <div className={`rounded-xl border ${colors.cardBorder} bg-white p-6 shadow-sm`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        
        {/* Left: Overall Posture & Score */}
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${colors.badge}`}>
              {posture.overall_posture || 'SECURE'}
            </span>
            <span className="text-xs text-slate-500 font-medium">Quantitative Risk Assessment</span>
          </div>

          <div className="flex items-baseline space-x-2">
            <span className="text-4xl sm:text-5xl font-black text-slate-900 tracking-tight">{score.toFixed(1)}</span>
            <span className="text-slate-400 font-semibold text-lg">/ 10.0</span>
            <span className="text-xs text-slate-500 ml-2 font-medium">CVSS-Aligned Severity Score</span>
          </div>

          {/* Progress Meter Bar */}
          <div className="w-full sm:w-80 h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className={`h-full transition-all duration-700 rounded-full ${colors.bar}`}
              style={{ width: `${scorePercent}%` }}
            />
          </div>
        </div>

        {/* Right: Severity Distribution Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-center min-w-[90px]">
            <span className="text-xs text-slate-500 font-medium">Critical</span>
            <p className="text-2xl font-bold text-red-600 mt-0.5">{posture.critical_count || 0}</p>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-center min-w-[90px]">
            <span className="text-xs text-slate-500 font-medium">High</span>
            <p className="text-2xl font-bold text-amber-600 mt-0.5">{posture.high_count || 0}</p>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-center min-w-[90px]">
            <span className="text-xs text-slate-500 font-medium">Medium</span>
            <p className="text-2xl font-bold text-yellow-600 mt-0.5">{posture.medium_count || 0}</p>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-center min-w-[90px]">
            <span className="text-xs text-slate-500 font-medium">Low / Pass</span>
            <p className="text-2xl font-bold text-emerald-600 mt-0.5">{posture.low_count || 0}</p>
          </div>

        </div>

      </div>
    </div>
  );
}
