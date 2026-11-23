import React, { useState } from 'react';
import { Server, Plus, CheckCircle, XCircle, Loader2, Trash2, ArrowUpRight } from 'lucide-react';
import { api } from '../api/client';

export default function TargetManager({ targets, selectedTarget, onSelectTarget, onRefreshTargets }) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [checkingId, setCheckingId] = useState(null);
  const [healthStatus, setHealthStatus] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // New Target Form State
  const [name, setName] = useState('');
  const [targetUrl, setTargetUrl] = useState('http://127.0.0.1:8001/query');
  const [description, setDescription] = useState('');
  const [apiKey, setApiKey] = useState('demo_synthetic_insecure_key_for_testing');

  const handleTestHealth = async (targetId, e) => {
    e.stopPropagation();
    setCheckingId(targetId);
    try {
      const res = await api.checkTargetHealth(targetId);
      setHealthStatus((prev) => ({ ...prev, [targetId]: res }));
    } catch (err) {
      setHealthStatus((prev) => ({
        ...prev,
        [targetId]: { is_reachable: false, message: err.message },
      }));
    } finally {
      setCheckingId(null);
    }
  };

  const handleCreateTarget = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await api.createTarget({
        name,
        target_url: targetUrl,
        description,
        api_key: apiKey,
      });
      setShowAddModal(false);
      setName('');
      setDescription('');
      onRefreshTargets();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Server className="w-5 h-5 text-teal-400" />
          <h2 className="text-base font-bold text-white">Target RAG Applications</h2>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold transition shadow"
        >
          <Plus className="w-4 h-4" />
          <span>Add Target</span>
        </button>
      </div>

      {/* Target Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {targets.length === 0 ? (
          <div className="col-span-full py-8 text-center text-slate-500 text-xs">
            No targets registered. Click "Add Target" to configure your first RAG application.
          </div>
        ) : (
          targets.map((tgt) => {
            const isSelected = selectedTarget?.id === tgt.id;
            const health = healthStatus[tgt.id];

            return (
              <div
                key={tgt.id}
                onClick={() => onSelectTarget(tgt)}
                className={`p-4 rounded-xl border cursor-pointer transition relative group ${
                  isSelected
                    ? 'bg-slate-800/90 border-teal-500 shadow-md shadow-teal-500/10'
                    : 'bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white group-hover:text-teal-400 transition">
                      {tgt.name}
                    </h3>
                    <p className="text-xs text-slate-400 font-mono mt-0.5 truncate max-w-[200px]">
                      {tgt.target_url}
                    </p>
                  </div>

                  {/* Connectivity Status Indicator */}
                  {health && (
                    <div className="flex items-center">
                      {health.is_reachable ? (
                        <span className="flex items-center text-[10px] text-emerald-400 bg-emerald-950/80 border border-emerald-800 px-2 py-0.5 rounded-full">
                          <CheckCircle className="w-3 h-3 mr-1" /> Online
                        </span>
                      ) : (
                        <span className="flex items-center text-[10px] text-rose-400 bg-rose-950/80 border border-rose-800 px-2 py-0.5 rounded-full" title={health.message}>
                          <XCircle className="w-3 h-3 mr-1" /> Offline
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {tgt.description && (
                  <p className="text-xs text-slate-400 mt-2 line-clamp-2">{tgt.description}</p>
                )}

                <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500">
                    Created {new Date(tgt.created_at).toLocaleDateString()}
                  </span>

                  <button
                    onClick={(e) => handleTestHealth(tgt.id, e)}
                    disabled={checkingId === tgt.id}
                    className="text-xs text-slate-300 hover:text-teal-400 flex items-center space-x-1 transition font-medium"
                  >
                    {checkingId === tgt.id ? (
                      <>
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>Testing...</span>
                      </>
                    ) : (
                      <>
                        <span>Check Status</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Add Target Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
            <h3 className="text-base font-bold text-white mb-4">Register RAG Target</h3>

            {error && (
              <div className="p-3 mb-4 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleCreateTarget} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Target Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Corporate RAG"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Query Endpoint URL</label>
                <input
                  type="url"
                  required
                  placeholder="http://127.0.0.1:8001/query"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">API Key / Token (Optional)</label>
                <input
                  type="password"
                  placeholder="Bearer token or API key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
                <textarea
                  rows="2"
                  placeholder="Brief summary of knowledge base contents and purpose"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold transition flex items-center space-x-2"
                >
                  {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Target</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
