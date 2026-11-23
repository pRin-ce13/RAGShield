import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import PostureCard from './components/PostureCard';
import TargetManager from './components/TargetManager';
import ScanConsole from './components/ScanConsole';
import FindingViewer from './components/FindingViewer';
import AuthModal from './components/AuthModal';
import { api } from './api/client';
import { Shield, LayoutDashboard, Server, RefreshCw } from 'lucide-react';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [backendOnline, setBackendOnline] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Core Data States
  const [targets, setTargets] = useState([]);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [activeScan, setActiveScan] = useState(null);
  const [findings, setFindings] = useState([]);
  const [posture, setPosture] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'targets'

  // 1. Initial Load: Check backend and load current user / targets
  useEffect(() => {
    checkHealthAndInit();
  }, []);

  const checkHealthAndInit = async () => {
    try {
      await api.checkBackendHealth();
      setBackendOnline(true);

      // Check current user
      if (api.getToken()) {
        try {
          const user = await api.getCurrentUser();
          setCurrentUser(user);
        } catch {
          api.logout();
          setCurrentUser(null);
        }
      }

      await loadTargets();
    } catch {
      setBackendOnline(false);
    }
  };

  const loadTargets = async () => {
    try {
      const data = await api.getTargets();
      setTargets(data);
      if (data.length > 0 && !selectedTarget) {
        setSelectedTarget(data[0]);
        // Load latest scan for default target
        loadLatestScanForTarget(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load targets:', err);
    }
  };

  const loadLatestScanForTarget = async (targetId) => {
    try {
      const scans = await api.getScans(targetId, 1);
      if (scans && scans.length > 0) {
        const latest = scans[0];
        setActiveScan(latest);
        if (latest.status === 'COMPLETED') {
          const [fList, post] = await Promise.all([
            api.getScanFindings(latest.id),
            api.getScanPosture(latest.id),
          ]);
          setFindings(fList);
          setPosture(post);
        }
      }
    } catch (err) {
      console.error('Failed to load latest scan:', err);
    }
  };

  // 2. Polling Loop for Active Scans
  useEffect(() => {
    if (!activeScan || (activeScan.status !== 'RUNNING' && activeScan.status !== 'PENDING')) {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const updated = await api.getScan(activeScan.id);
        setActiveScan(updated);

        if (updated.status === 'COMPLETED' || updated.status === 'FAILED') {
          clearInterval(pollInterval);
          if (updated.status === 'COMPLETED') {
            const [fList, post] = await Promise.all([
              api.getScanFindings(updated.id),
              api.getScanPosture(updated.id),
            ]);
            setFindings(fList);
            setPosture(post);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1500);

    return () => clearInterval(pollInterval);
  }, [activeScan]);

  const handleSelectTarget = (tgt) => {
    setSelectedTarget(tgt);
    loadLatestScanForTarget(tgt.id);
  };

  const handleScanLaunched = (scan) => {
    setActiveScan(scan);
    setFindings([]);
    setPosture(null);
  };

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <Navbar
        currentUser={currentUser}
        backendOnline={backendOnline}
        onOpenAuth={() => setShowAuthModal(true)}
        onLogout={handleLogout}
      />

      {/* Main Workspace Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Navigation Tabs Bar */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
                activeTab === 'dashboard'
                  ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Assessment Console</span>
            </button>

            <button
              onClick={() => setActiveTab('targets')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
                activeTab === 'targets'
                  ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <Server className="w-4 h-4" />
              <span>Target RAGs ({targets.length})</span>
            </button>
          </div>

          <button
            onClick={checkHealthAndInit}
            title="Refresh State"
            className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Tab 1: Dashboard View */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Executive Risk Posture Metric Card */}
            {posture && <PostureCard posture={posture} />}

            {/* Assessment Console (Launch & Progress) */}
            <ScanConsole
              target={selectedTarget}
              activeScan={activeScan}
              onScanLaunched={handleScanLaunched}
            />

            {/* Deduplicated Findings & Remediation Playbooks */}
            <FindingViewer findings={findings} />
          </div>
        )}

        {/* Tab 2: Target Management View */}
        {activeTab === 'targets' && (
          <div className="space-y-6">
            <TargetManager
              targets={targets}
              selectedTarget={selectedTarget}
              onSelectTarget={handleSelectTarget}
              onRefreshTargets={loadTargets}
            />
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        <p>RAGShield — Automated Security Evaluation & Vulnerability Assessment Platform for RAG Applications.</p>
      </footer>

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onAuthSuccess={(user) => setCurrentUser(user)}
      />
    </div>
  );
}
