import React, { useState } from 'react';
import { ShieldAlert, ChevronDown, ChevronUp, ExternalLink, Wrench, FileText, CheckCircle2, Download, FileJson, Loader2 } from 'lucide-react';
import { api } from '../api/client';

export default function FindingViewer({ findings, scanId }) {
  const [expandedId, setExpandedId] = useState(null);
  const [activeTab, setActiveTab] = useState('remediation'); // 'remediation' | 'evidence'
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [isExportingJson, setIsExportingJson] = useState(false);
  const [exportError, setExportError] = useState(null);

  const handleDownloadPdf = async () => {
    if (!scanId) return;
    setIsExportingPdf(true);
    setExportError(null);
    try {
      await api.downloadPdfReport(scanId);
    } catch (err) {
      setExportError(err.message);
    } finally {
      setIsExportingPdf(false);
    }
  };

  const handleDownloadJson = async () => {
    if (!scanId) return;
    setIsExportingJson(true);
    setExportError(null);
    try {
      await api.downloadJsonReport(scanId);
    } catch (err) {
      setExportError(err.message);
    } finally {
      setIsExportingJson(false);
    }
  };

  if (!findings || findings.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center shadow-sm">
        <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto mb-3" />
        <h3 className="text-sm font-bold text-slate-900">No Vulnerabilities Identified</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
          The target application conformed to evaluated security baselines. Run an automated assessment scan to discover security posture.
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
        return 'bg-red-50 text-red-700 border-red-200';
      case 'HIGH':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'MEDIUM':
        return 'bg-yellow-50 text-yellow-800 border-yellow-200';
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
      {/* Header bar with title and export buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-red-50 text-red-600 rounded-lg border border-red-100">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Vulnerability Findings</h2>
            <p className="text-xs text-slate-500">Root-cause defects identified during assessment</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-600 font-mono font-medium bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
            {findings.length} Defect{findings.length > 1 ? 's' : ''} Identified
          </span>

          {scanId && (
            <>
              {/* JSON Export Button */}
              <button
                onClick={handleDownloadJson}
                disabled={isExportingJson}
                title="Export standardized JSON audit report"
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold transition shadow-2xs"
              >
                {isExportingJson ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <FileJson className="w-3.5 h-3.5 text-blue-600" />
                )}
                <span>Export JSON</span>
              </button>

              {/* PDF Download Button */}
              <button
                onClick={handleDownloadPdf}
                disabled={isExportingPdf}
                title="Download publication-quality executive PDF report"
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition shadow-2xs"
              >
                {isExportingPdf ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Download className="w-3.5 h-3.5" />
                )}
                <span>Download PDF</span>
              </button>
            </>
          )}
        </div>
      </div>

      {exportError && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs">
          {exportError}
        </div>
      )}

      {/* Findings Accordion List */}
      <div className="space-y-3">
        {findings.map((f, idx) => {
          const isExpanded = expandedId === f.id;
          const sevClass = getSeverityStyle(f.severity);

          return (
            <div
              key={f.id || idx}
              className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs hover:border-slate-300 transition"
            >
              {/* Finding Header Item */}
              <div
                onClick={() => toggleExpand(f.id)}
                className="p-4 cursor-pointer hover:bg-slate-50/70 transition flex items-center justify-between gap-4"
              >
                <div className="flex items-start space-x-3.5">
                  <div className="flex flex-col items-center justify-center w-12 h-12 rounded-xl bg-slate-50 border border-slate-200 shrink-0">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">RISK</span>
                    <span className="text-sm font-black text-slate-900">{f.risk_score?.toFixed(1)}</span>
                  </div>

                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="text-xs font-mono font-bold text-slate-500">{f.finding_id}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${sevClass}`}>
                        {f.severity}
                      </span>
                      {f.owasp_category && (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 font-mono font-medium border border-slate-200">
                          {f.owasp_category}
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-bold text-slate-900">{f.title}</h3>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <span className="text-xs text-slate-500 hidden sm:inline font-medium">
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
                <div className="border-t border-slate-200 p-5 bg-slate-50/60 space-y-4 text-xs">
                  
                  {/* Technical Description */}
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">Technical Summary & Impact</h4>
                    <p className="text-slate-600 leading-relaxed">{f.description}</p>
                  </div>

                  {/* Tabs: Remediation vs Evidence */}
                  <div className="flex space-x-2 border-b border-slate-200 pb-2">
                    <button
                      onClick={() => setActiveTab('remediation')}
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-bold transition text-xs ${
                        activeTab === 'remediation'
                          ? 'bg-white text-slate-900 border border-slate-200 shadow-xs'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      <Wrench className="w-3.5 h-3.5 text-blue-600" />
                      <span>Remediation Playbook</span>
                    </button>

                    <button
                      onClick={() => setActiveTab('evidence')}
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-bold transition text-xs ${
                        activeTab === 'evidence'
                          ? 'bg-white text-slate-900 border border-slate-200 shadow-xs'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      <FileText className="w-3.5 h-3.5 text-blue-600" />
                      <span>Supporting Evidence ({f.evidence_count})</span>
                    </button>
                  </div>

                  {/* Tab Content: Remediation */}
                  {activeTab === 'remediation' && (
                    <div className="space-y-3 pt-1">
                      <div className="p-3.5 rounded-lg bg-blue-50/80 border border-blue-200 text-blue-900">
                        <span className="font-semibold block mb-0.5">High-Level Recommendation:</span>
                        <p className="leading-relaxed">{f.remediation_summary}</p>
                      </div>

                      <div>
                        <span className="font-semibold text-slate-800 block mb-2">Step-by-Step Engineering Guardrails:</span>
                        <ul className="space-y-2">
                          {(f.remediation_steps || []).map((step, sIdx) => (
                            <li key={sIdx} className="bg-white p-3 rounded-lg border border-slate-200 text-slate-800 font-mono text-[11px] leading-relaxed shadow-2xs">
                              {step}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {f.references && f.references.length > 0 && (
                        <div className="pt-2">
                          <span className="font-semibold text-slate-600 block mb-1.5">External References & OWASP Specs:</span>
                          <div className="flex flex-wrap gap-2">
                            {f.references.map((ref, rIdx) => (
                              <a
                                key={rIdx}
                                href={ref}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center space-x-1.5 text-[11px] text-blue-600 hover:underline bg-white px-2.5 py-1 rounded border border-slate-200 font-medium"
                              >
                                <span>{ref}</span>
                                <ExternalLink className="w-3 h-3 text-slate-400" />
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Tab Content: Forensic Evidence */}
                  {activeTab === 'evidence' && (
                    <div className="space-y-3 pt-1">
                      {(f.evidence_instances || []).map((ev, eIdx) => (
                        <div key={eIdx} className="bg-white p-4 rounded-xl border border-slate-200 space-y-2 font-mono text-[11px] shadow-2xs">
                          <div className="flex justify-between text-slate-600 pb-2 border-b border-slate-100">
                            <span className="text-blue-600 font-bold">[{ev.test_id}] {ev.test_name}</span>
                            <span>Latency: {ev.latency_ms?.toFixed(1)}ms</span>
                          </div>
                          {ev.target_role && (
                            <div className="text-slate-600">Caller Role: <span className="text-slate-900 font-semibold">{ev.target_role}</span></div>
                          )}
                          <div className="pt-1">
                            <span className="text-red-700 block font-semibold">Observed Leak Snippet:</span>
                            <pre className="p-3 bg-slate-50 rounded-lg text-red-800 border border-red-100 mt-1 whitespace-pre-wrap overflow-x-auto text-[11px] font-mono leading-relaxed">
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
