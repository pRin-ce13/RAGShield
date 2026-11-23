import React, { useState } from 'react';
import { ShieldAlert, ChevronDown, ChevronUp, ExternalLink, Wrench, FileText, CheckCircle2 } from 'lucide-react';

export default function FindingViewer({ findings }) {
  const [expandedId, setExpandedId] = useState(null);
  const [activeTab, setActiveTab] = useState('remediation'); // 'remediation' | 'evidence'

  if (!findings || findings.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center shadow-lg">
        <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
        <h3 className="text-sm font-bold text-white">No Vulnerabilities Identified</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          The target application conformed to evaluated security baselines. Run a scan to discover security posture.
        </p>
      </div>
    );
  }

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
    setActiveTab('remediation');
  };

  const getSeverityStyle = (sev) => {
    switch (sev?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-950/80 text-rose-300 border-rose-800';
      case 'HIGH':
        return 'bg-amber-950/80 text-amber-300 border-amber-800';
      case 'MEDIUM':
        return 'bg-yellow-950/80 text-yellow-300 border-yellow-800';
      default:
        return 'bg-blue-950/80 text-blue-300 border-blue-800';
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-5 h-5 text-rose-400" />
          <h2 className="text-base font-bold text-white">Deduplicated Vulnerability Findings</h2>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {findings.length} Root-Cause Defect{findings.length > 1 ? 's' : ''} Identified
        </span>
      </div>

      {/* Findings Accordion List */}
      <div className="space-y-3">
        {findings.map((f, idx) => {
          const isExpanded = expandedId === f.id;
          const sevClass = getSeverityStyle(f.severity);

          return (
            <div
              key={f.id || idx}
              className="bg-slate-950/60 border border-slate-800/80 rounded-xl overflow-hidden transition"
            >
              {/* Finding Header Item */}
              <div
                onClick={() => toggleExpand(f.id)}
                className="p-4 cursor-pointer hover:bg-slate-800/40 transition flex items-center justify-between gap-4"
              >
                <div className="flex items-start space-x-3">
                  <div className="flex flex-col items-center justify-center w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 shrink-0">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">RISK</span>
                    <span className="text-sm font-black text-rose-400">{f.risk_score?.toFixed(1)}</span>
                  </div>

                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="text-xs font-mono font-bold text-slate-400">{f.finding_id}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${sevClass}`}>
                        {f.severity}
                      </span>
                      {f.owasp_category && (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-mono">
                          {f.owasp_category}
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-bold text-white">{f.title}</h3>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <span className="text-xs text-slate-400 hidden sm:inline">
                    {f.evidence_count} Vector{f.evidence_count > 1 ? 's' : ''} Confirmed
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-slate-400" />
                  )}
                </div>
              </div>

              {/* Expanded Detail Drawer */}
              {isExpanded && (
                <div className="border-t border-slate-800/80 p-5 bg-slate-900/40 space-y-4 text-xs">
                  
                  {/* Technical Description */}
                  <div>
                    <h4 className="font-semibold text-slate-300 mb-1">Technical Summary & Impact</h4>
                    <p className="text-slate-400 leading-relaxed">{f.description}</p>
                  </div>

                  {/* Tabs: Remediation vs Evidence */}
                  <div className="flex space-x-2 border-b border-slate-800 pb-2">
                    <button
                      onClick={() => setActiveTab('remediation')}
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-bold transition ${
                        activeTab === 'remediation'
                          ? 'bg-teal-500/20 text-teal-400 border border-teal-500/40'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <Wrench className="w-3.5 h-3.5" />
                      <span>Remediation Playbook</span>
                    </button>

                    <button
                      onClick={() => setActiveTab('evidence')}
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-bold transition ${
                        activeTab === 'evidence'
                          ? 'bg-teal-500/20 text-teal-400 border border-teal-500/40'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Supporting Evidence ({f.evidence_count})</span>
                    </button>
                  </div>

                  {/* Tab Content: Remediation */}
                  {activeTab === 'remediation' && (
                    <div className="space-y-3 pt-1">
                      <div className="p-3 rounded-lg bg-teal-950/30 border border-teal-800/40 text-teal-300">
                        <span className="font-semibold block mb-0.5">High-Level Recommendation:</span>
                        {f.remediation_summary}
                      </div>

                      <div>
                        <span className="font-semibold text-slate-300 block mb-2">Step-by-Step Engineering Guardrails:</span>
                        <ul className="space-y-1.5">
                          {(f.remediation_steps || []).map((step, sIdx) => (
                            <li key={sIdx} className="bg-slate-950/60 p-2.5 rounded border border-slate-800/60 text-slate-300 font-mono text-[11px] leading-relaxed">
                              {step}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {f.references && f.references.length > 0 && (
                        <div className="pt-2">
                          <span className="font-semibold text-slate-400 block mb-1">External References & OWASP Specs:</span>
                          <div className="flex flex-wrap gap-2">
                            {f.references.map((ref, rIdx) => (
                              <a
                                key={rIdx}
                                href={ref}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center space-x-1 text-[11px] text-teal-400 hover:underline bg-slate-950 px-2.5 py-1 rounded border border-slate-800"
                              >
                                <span>{ref}</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Tab Content: Forensic Evidence */}
                  {activeTab === 'evidence' && (
                    <div className="space-y-2 pt-1">
                      {(f.evidence_instances || []).map((ev, eIdx) => (
                        <div key={eIdx} className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1 font-mono text-[11px]">
                          <div className="flex justify-between text-slate-400 pb-1 border-b border-slate-900">
                            <span className="text-teal-400 font-bold">[{ev.test_id}] {ev.test_name}</span>
                            <span>Latency: {ev.latency_ms?.toFixed(1)}ms</span>
                          </div>
                          {ev.target_role && (
                            <div className="text-slate-400">Caller Role: <span className="text-slate-200">{ev.target_role}</span></div>
                          )}
                          <div className="pt-1">
                            <span className="text-rose-400 block font-semibold">Observed Leak Snippet:</span>
                            <pre className="p-2 bg-slate-900/90 rounded text-rose-300 mt-1 whitespace-pre-wrap overflow-x-auto text-[11px]">
                              {ev.evidence_snippet}
                            </pre>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
