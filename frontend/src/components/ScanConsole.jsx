import React, { useState } from 'react';
import { Play, Loader2, ShieldCheck, Filter, Cpu, Clock, CheckCircle, AlertTriangle } from 'lucide-react';
import { api } from '../api/client';

const CATEGORIES = [
  { id: 'direct_prompt_injection', label: 'Direct Prompt Injection', desc: 'System override & jailbreak instructions' },
  { id: 'unauthorized_retrieval', label: 'Unauthorized Retrieval', desc: 'RBAC boundary bypass & cross-department leaks' },
  { id: 'sensitive_data_disclosure', label: 'Sensitive Data Disclosure', desc: 'Credential & synthetic secret exposure' },
  { id: 'retrieval_manipulation', label: 'Retrieval Manipulation', desc: 'Semantic collision & context drift' },
];

export default function ScanConsole({ target, activeScan, onScanLaunched }) {
  const [selectedCategories, setSelectedCategories] = useState([
    'direct_prompt_injection',
    'unauthorized_retrieval',
    'sensitive_data_disclosure',
    'retrieval_manipulation',
  ]);
  const [concurrency, setConcurrency] = useState(3);
  const [timeout, setTimeoutVal] = useState(15.0);
  const [isLaunching, setIsLaunching] = useState(false);
  const [launchError, setLaunchError] = useState(null);

  const toggleCategory = (catId) => {
    setSelectedCategories((prev) =>
      prev.includes(catId) ? prev.filter((id) => id !== catId) : [...prev, catId]
    );
  };

  const handleLaunchScan = async () => {
    if (!target) return;
    setIsLaunching(true);
    setLaunchError(null);

    try {
      const scan = await api.launchScan({
        target_id: target.id,
        categories: selectedCategories.length > 0 ? selectedCategories : null,
        max_concurrency: concurrency,
        timeout_seconds: timeout,
      });
      onScanLaunched(scan);
    } catch (err) {
      setLaunchError(err.message);
    } finally {
      setIsLaunching(false);
    }
  };

  const isScanning = activeScan && (activeScan.status === 'RUNNING' || activeScan.status === 'PENDING');

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-teal-400" />
            <span>Automated Security Scanner</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Target:{' '}
            <span className="font-semibold text-slate-200">
              {target ? target.name : 'No Target Selected'}
            </span>
          </p>
        </div>

        {/* Launch Button */}
        <button
          onClick={handleLaunchScan}
          disabled={!target || isScanning || isLaunching}
          className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl font-bold text-sm transition shadow-lg ${
            !target || isScanning
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
              : 'bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 shadow-teal-500/20'
          }`}
        >
          {isScanning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-teal-400" />
              <span>Assessment Running...</span>
            </>
          ) : isLaunching ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Dispatching...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Launch Security Assessment</span>
            </>
          )}
        </button>
      </div>

      {launchError && (
        <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-xs">
          {launchError}
        </div>
      )}

      {/* Live Status Bar if scan is active or recently completed */}
      {activeScan && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <span className={`w-2.5 h-2.5 rounded-full ${
                activeScan.status === 'COMPLETED' ? 'bg-emerald-400' :
                activeScan.status === 'RUNNING' ? 'bg-teal-400 animate-pulse' :
                activeScan.status === 'FAILED' ? 'bg-rose-500' : 'bg-amber-400'
              }`} />
              <span className="font-semibold text-white">Scan ID: {activeScan.id}</span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-400 uppercase font-mono tracking-wider">{activeScan.status}</span>
            </div>

            <div className="text-slate-400 font-mono text-[11px]">
              {activeScan.completed_tests} / {activeScan.total_tests || 11} Probes Executed
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                activeScan.status === 'COMPLETED' ? 'bg-emerald-500' :
                activeScan.status === 'FAILED' ? 'bg-rose-500' : 'bg-teal-500'
              }`}
              style={{
                width: `${activeScan.total_tests ? Math.round((activeScan.completed_tests / activeScan.total_tests) * 100) : (isScanning ? 35 : 100)}%`,
              }}
            />
          </div>

          {activeScan.error_message && (
            <p className="text-xs text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-900/60 font-mono">
              Diagnostics: {activeScan.error_message}
            </p>
          )}
        </div>
      )}

      {/* Attack Suite Categories */}
      <div className="space-y-3">
        <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
          <Filter className="w-3.5 h-3.5 text-teal-400" />
          <span>Evaluation Attack Suite</span>
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {CATEGORIES.map((cat) => {
            const isChecked = selectedCategories.includes(cat.id);
            return (
              <div
                key={cat.id}
                onClick={() => !isScanning && toggleCategory(cat.id)}
                className={`p-3 rounded-xl border transition cursor-pointer flex items-start space-x-3 ${
                  isChecked
                    ? 'bg-slate-800/80 border-teal-500/60 text-white'
                    : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700'
                } ${isScanning ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  readOnly
                  className="mt-0.5 rounded border-slate-700 text-teal-500 focus:ring-0"
                />
                <div>
                  <h4 className="text-xs font-bold text-slate-200">{cat.label}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">{cat.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Concurrency and Timeout Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800/60">
        <div>
          <div className="flex justify-between text-xs text-slate-300 mb-1">
            <span>Concurrency Throttle:</span>
            <span className="font-mono text-teal-400 font-bold">{concurrency} Simultaneous Probes</span>
          </div>
          <input
            type="range"
            min="1"
            max="5"
            value={concurrency}
            disabled={isScanning}
            onChange={(e) => setConcurrency(parseInt(e.target.value))}
            className="w-full accent-teal-500 cursor-pointer"
          />
        </div>

        <div>
          <div className="flex justify-between text-xs text-slate-300 mb-1">
            <span>Per-Probe Timeout:</span>
            <span className="font-mono text-teal-400 font-bold">{timeout.toFixed(0)} Seconds</span>
          </div>
          <input
            type="range"
            min="5"
            max="30"
            step="5"
            value={timeout}
            disabled={isScanning}
            onChange={(e) => setTimeoutVal(parseFloat(e.target.value))}
            className="w-full accent-teal-500 cursor-pointer"
          />
        </div>
      </div>

    </div>
  );
}
