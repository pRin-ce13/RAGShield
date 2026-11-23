import React, { useState } from 'react';
import { Play, Loader2, ShieldCheck, Filter, Cpu, Clock, CheckCircle, AlertTriangle } from 'lucide-react';
import { api } from '../api/client';

const CATEGORIES = [
  { id: 'direct_prompt_injection', label: 'Direct Prompt Injection', desc: 'System override & jailbreak instructions' },
  { id: 'unauthorized_retrieval', label: 'Unauthorized Retrieval', desc: 'RBAC boundary bypass & cross-department leaks' },
  { id: 'sensitive_data_disclosure', label: 'Sensitive Data Disclosure', desc: 'Credential & synthetic secret exposure' },
  { id: 'retrieval_manipulation', label: 'Retrieval Manipulation', desc: 'Semantic collision & context drift' },
  { id: 'multi_turn_injection', label: 'Multi-Turn Injection', desc: 'Conversational escalation & progressive trust erosion' },
  { id: 'privilege_escalation', label: 'Privilege Escalation', desc: 'Contextual persona overriding to access control bypass' },
  { id: 'resource_exhaustion_dos', label: 'Resource Exhaustion (DoS)', desc: 'Context window flooding & high-token stress probes' },
];

export default function ScanConsole({ target, activeScan, onScanLaunched }) {
  const [selectedCategories, setSelectedCategories] = useState([
    'direct_prompt_injection',
    'unauthorized_retrieval',
    'sensitive_data_disclosure',
    'retrieval_manipulation',
    'multi_turn_injection',
    'privilege_escalation',
    'resource_exhaustion_dos',
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
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-50 text-blue-600 rounded-lg border border-blue-100">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Automated Security Scanner</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Active Target:{' '}
              <span className="font-semibold text-slate-800">
                {target ? target.name : 'No Target Selected'}
              </span>
            </p>
          </div>
        </div>

        {/* Launch Button */}
        <button
          onClick={handleLaunchScan}
          disabled={!target || isScanning || isLaunching}
          className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition shadow-sm ${
            !target || isScanning
              ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
              : 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-500/10'
          }`}
        >
          {isScanning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-white" />
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
        <div className="p-3.5 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs">
          {launchError}
        </div>
      )}

      {/* Live Status Bar if scan is active or recently completed */}
      {activeScan && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <span className={`w-2.5 h-2.5 rounded-full ${
                activeScan.status === 'COMPLETED' ? 'bg-emerald-500' :
                activeScan.status === 'RUNNING' ? 'bg-blue-600 animate-pulse' :
                activeScan.status === 'FAILED' ? 'bg-red-500' : 'bg-amber-500'
              }`} />
              <span className="font-semibold text-slate-900">Scan ID: {activeScan.id}</span>
              <span className="text-slate-300">|</span>
              <span className="text-slate-600 uppercase font-mono tracking-wider text-[11px] font-semibold">{activeScan.status}</span>
            </div>

            <div className="text-slate-600 font-mono text-xs">
              {activeScan.completed_tests} / {activeScan.total_tests || 18} Probes Executed
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden border border-slate-200">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                activeScan.status === 'COMPLETED' ? 'bg-emerald-500' :
                activeScan.status === 'FAILED' ? 'bg-red-500' : 'bg-blue-600'
              }`}
              style={{
                width: `${activeScan.total_tests ? Math.round((activeScan.completed_tests / activeScan.total_tests) * 100) : (isScanning ? 35 : 100)}%`,
              }}
            />
          </div>

          {activeScan.error_message && (
            <p className="text-xs text-red-700 bg-red-50 p-2.5 rounded-lg border border-red-200 font-mono">
              Diagnostics: {activeScan.error_message}
            </p>
          )}
        </div>
      )}

      {/* Attack Suite Categories */}
      <div className="space-y-3">
        <label className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
          <Filter className="w-3.5 h-3.5 text-blue-600" />
          <span>Evaluation Attack Suite</span>
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {CATEGORIES.map((cat) => {
            const isChecked = selectedCategories.includes(cat.id);
            return (
              <div
                key={cat.id}
                onClick={() => !isScanning && toggleCategory(cat.id)}
                className={`p-3.5 rounded-xl border transition cursor-pointer flex items-start space-x-3 ${
                  isChecked
                    ? 'bg-blue-50/50 border-blue-400 text-slate-900 shadow-xs'
                    : 'bg-slate-50/50 border-slate-200 text-slate-600 hover:border-slate-300'
                } ${isScanning ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  readOnly
                  className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-0"
                />
                <div>
                  <h4 className="text-xs font-bold text-slate-900">{cat.label}</h4>
                  <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">{cat.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Concurrency and Timeout Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-3 border-t border-slate-100">
        <div>
          <div className="flex justify-between text-xs text-slate-700 mb-1.5 font-medium">
            <span>Concurrency Throttle:</span>
            <span className="font-mono text-blue-600 font-bold">{concurrency} Simultaneous Probes</span>
          </div>
          <input
            type="range"
            min="1"
            max="5"
            value={concurrency}
            disabled={isScanning}
            onChange={(e) => setConcurrency(parseInt(e.target.value))}
            className="w-full accent-blue-600 cursor-pointer"
          />
        </div>

        <div>
          <div className="flex justify-between text-xs text-slate-700 mb-1.5 font-medium">
            <span>Per-Probe Timeout:</span>
            <span className="font-mono text-blue-600 font-bold">{timeout.toFixed(0)} Seconds</span>
          </div>
          <input
            type="range"
            min="5"
            max="30"
            step="5"
            value={timeout}
            disabled={isScanning}
            onChange={(e) => setTimeoutVal(parseFloat(e.target.value))}
            className="w-full accent-blue-600 cursor-pointer"
          />
        </div>
      </div>

    </div>
  );
}
