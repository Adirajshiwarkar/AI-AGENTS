import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Sparkles, 
  Compass, 
  Settings, 
  LogOut, 
  ArrowRight, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  Download, 
  History, 
  Layers, 
  FileCheck, 
  Eye, 
  Terminal, 
  User, 
  Lock, 
  PlusCircle, 
  Calendar,
  ExternalLink
} from 'lucide-react';

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:8000' : '';

const getLogStyleAndIcon = (log) => {
  const text = log.trim();
  if (text.startsWith('[SYSTEM]')) {
    return { className: 'text-indigo-300 font-semibold', icon: '⚙️' };
  }
  if (text.startsWith('[PLANNER]')) {
    return { className: 'text-cyan-300 font-semibold', icon: '📋' };
  }
  if (text.startsWith('[REFLECTION]') || text.startsWith('[STEP] Reflection Phase') || text.includes('Self-Check') || text.includes('Sanity check')) {
    return { className: 'text-amber-300 font-semibold', icon: '🔍' };
  }
  if (text.includes('Executing Task') || text.includes('executed successfully')) {
    return { className: 'text-sky-300', icon: '⚡' };
  }
  if (text.includes('Generating section') || text.includes('Successfully regenerated') || text.includes('Regenerating failed sections')) {
    return { className: 'text-emerald-300', icon: '✍️' };
  }
  if (text.includes('Document successfully saved') || text.includes('succeeded') || text.includes('Completed Successfully')) {
    return { className: 'text-green-400 font-bold', icon: '✅' };
  }
  if (text.toLowerCase().includes('failed') || text.toLowerCase().includes('exception') || text.toLowerCase().includes('error')) {
    return { className: 'text-red-400 font-semibold', icon: '❌' };
  }
  return { className: 'text-slate-400', icon: '•' };
};

export default function App() {
  // Auth state
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [username, setUsername] = useState(localStorage.getItem('username') || '');
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'
  
  // Auth Form Inputs
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // Document Generator state
  const [requestText, setRequestText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [elapsedTime, setElapsedTime] = useState(0);
  const [timerInterval, setTimerInterval] = useState(null);
  
  // Active Agent Phase for loading simulation
  const [agentPhase, setAgentPhase] = useState(0); // 0: Idle, 1: Planning, 2: Executing, 3: Reflecting, 4: Verifying
  const [agentLog, setAgentLog] = useState([]);

  // Result state
  const [result, setResult] = useState(null);
  const [selectedSection, setSelectedSection] = useState(null);
  const [resultTab, setResultTab] = useState('preview'); // 'preview', 'logs', 'assumptions'

  // User document history (saved in localStorage per user)
  const [history, setHistory] = useState([]);

  // Templates to help the user start
  const templates = [
    {
      title: "AI Chatbot Customer Support",
      prompt: "Generate a project proposal for implementing an AI chatbot for customer support."
    },
    {
      title: "ERP Migration Plan",
      prompt: "We need a technical implementation plan for migrating our legacy monolithic ERP to microservices in six months with a small engineering team and uncertain budget. Make reasonable assumptions."
    },
    {
      title: "Cybersecurity Incident Response SOP",
      prompt: "Create a standard operating procedure (SOP) for cybersecurity incident response in a medium-sized fintech company, detailing critical escalation paths."
    }
  ];

  // Fetch current user details if token is valid
  useEffect(() => {
    if (token) {
      fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => {
        if (!res.ok) {
          handleLogout();
        }
      })
      .catch(() => {
        // If offline, keep local session
      });
      
      // Load user history
      const savedHistory = localStorage.getItem(`history_${username}`);
      if (savedHistory) {
        setHistory(JSON.parse(savedHistory));
      }
    }
  }, [token, username]);

  // Timer counter
  useEffect(() => {
    if (loading) {
      const start = Date.now();
      const interval = setInterval(() => {
        setElapsedTime(Math.round((Date.now() - start) / 1000));
      }, 1000);
      setTimerInterval(interval);
      return () => clearInterval(interval);
    } else {
      if (timerInterval) {
        clearInterval(timerInterval);
        setTimerInterval(null);
      }
    }
  }, [loading]);

  const logEndRef = React.useRef(null);

  // Auto-scroll logs to bottom as they arrive
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [agentLog]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setToken('');
    setUsername('');
    setResult(null);
    setHistory([]);
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthLoading(true);

    if (!authUsername.trim() || !authPassword.trim()) {
      setAuthError('Please fill in all fields.');
      setAuthLoading(false);
      return;
    }

    const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register';

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: authUsername.trim(),
          password: authPassword.trim()
        })
      });

      const data = await res.json();
      
      if (!res.ok) {
        let errMsg = data.detail || data.message || 'Authentication failed';
        if (data.errors && Array.isArray(data.errors)) {
          errMsg = data.errors.map(e => `${e.field.replace('body.', '')}: ${e.message}`).join(', ');
        }
        throw new Error(errMsg);
      }

      if (authMode === 'register') {
        // Automatically switch to login on registration
        setAuthMode('login');
        setAuthUsername(authUsername.trim());
        setAuthPassword('');
        setAuthError('Registration successful! Please login.');
      } else {
        // Login success
        localStorage.setItem('token', data.token);
        localStorage.setItem('username', data.username);
        setToken(data.token);
        setUsername(data.username);
        setAuthUsername('');
        setAuthPassword('');
      }
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!requestText.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);
    setAgentPhase(1);
    setAgentLog(["[SYSTEM] Connecting to document generation agent..."]);
    setElapsedTime(0);

    try {
      const res = await fetch(`${API_BASE}/agent`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ request: requestText.trim() })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.message || (errData.detail && errData.detail.summary) || 'Failed to generate document');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let finalResult = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Save the last partial line back to the buffer
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed.type === 'log') {
              setAgentLog(prev => [...prev, parsed.message]);
              
              // Map log messages to corresponding UI stepper phases
              const msg = parsed.message.toLowerCase();
              if (msg.includes('planning phase') || msg.includes('planning process')) {
                setAgentPhase(1);
              } else if (msg.includes('execution phase') || msg.includes('executing task') || msg.includes('generating section')) {
                setAgentPhase(2);
              } else if (msg.includes('reflection phase') || msg.includes('self-check')) {
                setAgentPhase(3);
              } else if (msg.includes('document generation') || msg.includes('compiling markdown') || msg.includes('re-generating')) {
                setAgentPhase(4);
              }
            } else if (parsed.type === 'result') {
              finalResult = parsed.data;
            } else if (parsed.type === 'error') {
              throw new Error(parsed.message);
            }
          } catch (e) {
            console.error('Failed to parse stream line:', line, e);
            if (e.message && e.message !== 'Unexpected end of JSON input') {
              throw e;
            }
          }
        }
      }

      if (!finalResult) {
        throw new Error('Agent execution finished without returning a result.');
      }

      setResult(finalResult);
      if (finalResult.sections_content && Object.keys(finalResult.sections_content).length > 0) {
        setSelectedSection(Object.keys(finalResult.sections_content)[0]);
      }

      // Add to user history
      const newHistoryItem = {
        id: Date.now(),
        request: requestText.trim(),
        summary: finalResult.summary,
        document_path: finalResult.document_path,
        execution_time: finalResult.execution_time,
        created_at: new Date().toLocaleString(),
        sections_content: finalResult.sections_content,
        assumptions: finalResult.assumptions,
        reflection_result: finalResult.reflection_result,
        completed_tasks: finalResult.completed_tasks,
        execution_plan: finalResult.execution_plan
      };

      setHistory(prev => {
        const updated = [newHistoryItem, ...prev.slice(0, 19)];
        localStorage.setItem(`history_${username}`, JSON.stringify(updated));
        return updated;
      });

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadFromHistory = (item) => {
    setRequestText(item.request);
    setResult(item);
    if (item.sections_content && Object.keys(item.sections_content).length > 0) {
      setSelectedSection(Object.keys(item.sections_content)[0]);
    }
  };

  const getDownloadUrl = (path) => {
    if (!path) return '';
    const filename = path.split('/').pop();
    return `${API_BASE}/download/${filename}`;
  };

  // Custom markdown-to-react element renderer
  const renderMarkdown = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    
    let inTable = false;
    let tableRows = [];

    const flushTable = (key) => {
      if (tableRows.length === 0) return null;
      const headers = tableRows[0];
      const body = tableRows.slice(1);
      
      const rendered = (
        <div key={key} className="my-6 overflow-x-auto rounded-lg border border-white/10">
          <table className="min-w-full divide-y divide-white/10 text-left">
            <thead className="bg-white/5">
              <tr>
                {headers.map((h, i) => (
                  <th key={i} className="px-4 py-3 text-sm font-semibold text-white">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 bg-transparent">
              {body.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-white/2 animate-fade-in">
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="px-4 py-2.5 text-sm text-slate-300">{renderInlineBold(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableRows = [];
      inTable = false;
      return rendered;
    };

    const elements = [];

    for (let idx = 0; idx < lines.length; idx++) {
      const line = lines[idx];
      const trimmed = line.trim();

      // Table line checking
      if (trimmed.startsWith('|')) {
        inTable = true;
        // Parse markdown table cells
        const cells = trimmed.split('|').map(c => c.trim()).filter((c, i, arr) => i > 0 && i < arr.length - 1);
        
        // Skip separator line (e.g. |---|---|)
        const isSeparator = cells.every(c => c.split('').every(ch => ch === '-' || ch === ':' || ch === ' '));
        if (!isSeparator) {
          tableRows.push(cells);
        }
        continue;
      } else if (inTable) {
        elements.push(flushTable(`table-${idx}`));
      }

      if (!trimmed) {
        elements.push(<div key={`empty-${idx}`} className="h-3" />);
        continue;
      }

      // H3 heading
      if (trimmed.startsWith('### ')) {
        elements.push(<h3 key={idx} className="text-xl font-bold mt-6 mb-3 text-indigo-400 font-display">{trimmed.slice(4)}</h3>);
        continue;
      }
      
      // H4 heading
      if (trimmed.startsWith('#### ')) {
        elements.push(<h4 key={idx} className="text-lg font-semibold mt-4 mb-2 text-cyan-400 font-display">{trimmed.slice(5)}</h4>);
        continue;
      }

      // Bullet items
      if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
        elements.push(
          <li key={idx} className="ml-5 list-disc my-1.5 text-slate-300">
            {renderInlineBold(trimmed.slice(2))}
          </li>
        );
        continue;
      }

      // Paragraph
      elements.push(
        <p key={idx} className="mb-3.5 text-slate-300 leading-relaxed text-base">
          {renderInlineBold(trimmed)}
        </p>
      );
    }

    if (inTable) {
      elements.push(flushTable(`table-end`));
    }

    return elements;
  };

  const renderInlineBold = (text) => {
    const parts = text.split('**');
    return parts.map((part, i) => i % 2 === 1 ? <strong key={i} className="text-white font-semibold">{part}</strong> : part);
  };

  // Auth Screen
  if (!token) {
    return (
      <div className="app-container justify-center items-center px-4 relative">
        <div className="glow-accent top-1/4 left-1/3 bg-indigo-600" />
        <div className="glow-accent bottom-1/4 right-1/3 bg-cyan-600" />

        <div className="glass-card w-full max-w-md p-8 relative z-10 animate-fade-in">
          <div className="text-center mb-8">
            <div className="inline-flex p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl mb-4">
              <Sparkles className="w-8 h-8 text-indigo-400" />
            </div>
            <h1 className="text-2xl font-bold font-display tracking-tight text-white mb-2">
              Autonomous Doc Engine
            </h1>
            <p className="text-sm text-slate-400">
              Create professional, client-ready business proposals and technical documents instantly.
            </p>
          </div>

          <form onSubmit={handleAuthSubmit} className="space-y-5">
            <div className="input-group">
              <label className="input-label">Username</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                  <User className="w-5 h-5" />
                </span>
                <input 
                  type="text" 
                  className="input-field w-full pl-11"
                  placeholder="Enter username"
                  value={authUsername}
                  onChange={(e) => setAuthUsername(e.target.value)}
                />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Password</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                  <Lock className="w-5 h-5" />
                </span>
                <input 
                  type="password" 
                  className="input-field w-full pl-11"
                  placeholder="Enter password"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                />
              </div>
            </div>

            {authError && (
              <div className="p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-2.5 text-sm text-red-300">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <span>{authError}</span>
              </div>
            )}

            <button 
              type="submit" 
              className="btn btn-primary w-full py-3"
              disabled={authLoading}
            >
              {authLoading ? (
                <Loader2 className="w-5 h-5 loader-spin" />
              ) : (
                <>
                  <span>{authMode === 'login' ? 'Login Session' : 'Create Account'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="text-center mt-6 pt-6 border-t border-white/5">
            <button 
              onClick={() => {
                setAuthMode(authMode === 'login' ? 'register' : 'login');
                setAuthError('');
              }}
              className="text-sm text-slate-400 hover:text-white transition-colors"
            >
              {authMode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Log in'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Dashboard Screen
  return (
    <div className="app-container">
      {/* Glow overlays */}
      <div className="glow-accent top-[-100px] right-0 bg-indigo-900/30" />
      <div className="glow-accent bottom-0 left-0 bg-cyan-900/20" />

      {/* Header bar */}
      <header className="border-b border-white/5 bg-slate-950/40 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
            <Sparkles className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-lg font-bold font-display text-white leading-none">Autonomous Doc Engine</h1>
            <span className="text-xs text-slate-400">Enterprise AI Generator</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 border border-white/5 rounded-xl">
            <User className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-semibold text-slate-200">{username}</span>
          </div>
          <button 
            onClick={handleLogout}
            className="p-2.5 bg-red-500/5 hover:bg-red-500/10 border border-red-500/10 hover:border-red-500/20 text-red-400 rounded-xl transition-all"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Body content */}
      <div className="main-content">
        {/* Sidebar panel */}
        <aside className="w-80 border-r border-white/5 bg-slate-950/20 backdrop-blur-sm p-6 overflow-y-auto hidden md:flex flex-col gap-6 shrink-0">
          <div className="flex items-center gap-2 text-slate-300 font-semibold font-display text-sm tracking-wider uppercase">
            <History className="w-4 h-4 text-indigo-400" />
            <span>Document Library</span>
          </div>

          <div className="flex-1 space-y-3">
            {history.length === 0 ? (
              <div className="h-40 border border-dashed border-white/5 rounded-2xl flex flex-col justify-center items-center text-center p-4">
                <FileText className="w-8 h-8 text-slate-600 mb-2" />
                <p className="text-xs text-slate-500">No generated files yet. Write a prompt to begin!</p>
              </div>
            ) : (
              history.map(item => (
                <div 
                  key={item.id} 
                  onClick={() => loadFromHistory(item)}
                  className={`p-3.5 border rounded-xl cursor-pointer text-left transition-all ${
                    result?.id === item.id 
                      ? 'bg-indigo-500/10 border-indigo-500/30' 
                      : 'bg-white/2 border-white/5 hover:border-white/10 hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-cyan-400" />
                      {item.created_at.split(',')[0]}
                    </span>
                    <a 
                      href={getDownloadUrl(item.document_path)}
                      download
                      onClick={(e) => e.stopPropagation()}
                      className="p-1 text-slate-400 hover:text-white rounded bg-white/5 hover:bg-white/10 transition-colors"
                      title="Download DOCX"
                    >
                      <Download className="w-3 h-3" />
                    </a>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-200 line-clamp-1 mb-1">{item.request}</h4>
                  <p className="text-xs text-slate-400 line-clamp-2">{item.summary}</p>
                </div>
              ))
            )}
          </div>

          <div className="pt-4 border-t border-white/5">
            <div className="p-3.5 bg-indigo-500/5 border border-indigo-500/10 rounded-2xl flex items-start gap-3">
              <Compass className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
              <div>
                <h5 className="text-xs font-semibold text-indigo-300">Fast API Host</h5>
                <p className="text-[11px] text-slate-400 break-all">{API_BASE}</p>
              </div>
            </div>
          </div>
        </aside>

        {/* Workspace panel */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto flex flex-col gap-8">
          {/* Prompt workspace card */}
          <div className="glass-card p-6 md:p-8">
            <div className="mb-6">
              <h2 className="text-xl font-bold font-display text-white mb-1">Create Document Request</h2>
              <p className="text-sm text-slate-400">Describe the business file you need. The autonomous agent will research details, structure the components, and format a professional document.</p>
            </div>

            <form onSubmit={handleGenerate} className="space-y-6">
              <div className="relative">
                <textarea 
                  className="input-field textarea-field w-full pl-4 pr-4 pt-4 text-base"
                  placeholder="E.g., I need a comprehensive business plan for a mobile health app startup focusing on telemedicine..."
                  value={requestText}
                  onChange={(e) => setRequestText(e.target.value)}
                  disabled={loading}
                />
              </div>

              {/* Templates */}
              <div>
                <span className="text-xs font-semibold text-slate-400 block mb-2.5 uppercase tracking-wider font-display">Quick Templates</span>
                <div className="flex flex-wrap gap-2.5">
                  {templates.map((tpl, i) => (
                    <button 
                      key={i}
                      type="button"
                      onClick={() => setRequestText(tpl.prompt)}
                      className="px-3.5 py-2 bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/10 rounded-xl text-xs text-slate-300 hover:text-white transition-all text-left"
                      disabled={loading}
                    >
                      {tpl.title}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-white/5">
                <div className="text-xs text-slate-400 max-w-[70%] truncate">
                  {loading && (
                    <span className="flex items-center gap-2 text-indigo-400 font-medium animate-pulse">
                      <Loader2 className="w-3.5 h-3.5 loader-spin shrink-0" />
                      <span>
                        {agentLog.length > 0 
                          ? agentLog[agentLog.length - 1] 
                          : `Initializing Agent (Elapsed: ${elapsedTime}s)...`
                        }
                      </span>
                    </span>
                  )}
                </div>
                
                <button 
                  type="submit" 
                  className="btn btn-primary px-6"
                  disabled={loading || !requestText.trim()}
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 loader-spin" />
                      <span>Agent Processing...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 text-cyan-300" />
                      <span>Generate Document</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex gap-3 text-red-300 animate-fade-in">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-sm">Failed to Generate Document</h4>
                <p className="text-xs mt-1 text-red-400/90">{error}</p>
              </div>
            </div>
          )}

          {/* Loading Stepper Progress */}
          {loading && (
            <div className="glass-card p-6 md:p-8 animate-fade-in space-y-6">
              <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <h3 className="font-bold font-display text-white flex items-center gap-2">
                  <Terminal className="w-5 h-5 text-indigo-400" />
                  Agent Execution Process
                </h3>
                <span className="px-2.5 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg text-xs font-semibold">
                  Active
                </span>
              </div>

              {/* Steps progress bar */}
              <div className="grid grid-cols-4 gap-4 relative">
                {[
                  { title: "Plan", label: "Analyze request" },
                  { title: "Draft", label: "Generate chapters" },
                  { title: "Review", label: "QA Validation" },
                  { title: "Verify", label: "Save package" }
                ].map((step, idx) => {
                  const stepNum = idx + 1;
                  const isCompleted = agentPhase > stepNum;
                  const isActive = agentPhase === stepNum;
                  return (
                    <div key={idx} className="flex flex-col items-center text-center relative z-10">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center border text-xs font-bold transition-all ${
                        isCompleted 
                          ? 'bg-success border-success text-white' 
                          : isActive 
                            ? 'bg-indigo-500 border-indigo-500 text-white shadow-lg shadow-indigo-500/20' 
                            : 'bg-white/5 border-white/10 text-slate-500'
                      }`}>
                        {isCompleted ? <CheckCircle className="w-4 h-4" /> : stepNum}
                      </div>
                      <span className={`text-xs font-semibold mt-2.5 ${isActive ? 'text-indigo-400' : isCompleted ? 'text-slate-200' : 'text-slate-500'}`}>{step.title}</span>
                      <span className="text-[10px] text-slate-500 hidden sm:block mt-0.5">{step.label}</span>
                    </div>
                  );
                })}
              </div>

              {/* Claude-style Thinking Visualizer */}
              <div className="p-4 bg-indigo-500/5 border border-indigo-500/10 rounded-xl flex items-center justify-between gap-4 animate-fade-in">
                <div className="flex items-center gap-3">
                  <div className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
                  </div>
                  <span className="text-xs font-semibold text-indigo-300 font-display uppercase tracking-wider animate-pulse">
                    {agentPhase === 1 && "Agent is analyzing intent & planning layout..."}
                    {agentPhase === 2 && "Agent is executing generation tasks..."}
                    {agentPhase === 3 && "Agent is validating and checking quality..."}
                    {agentPhase === 4 && "Agent is generating styled DOCX package..."}
                    {!agentPhase && "Agent is thinking..."}
                  </span>
                </div>
                
                {/* Wavy Pulse Bars */}
                <div className="flex items-center gap-1.5">
                  <span className="thinking-wave-bar"></span>
                  <span className="thinking-wave-bar"></span>
                  <span className="thinking-wave-bar"></span>
                  <span className="thinking-wave-bar"></span>
                  <span className="thinking-wave-bar"></span>
                </div>
              </div>

              {/* Log view */}
              <div className="bg-black/40 border border-white/5 rounded-xl p-4 font-mono text-[11px] text-slate-400 h-40 overflow-y-auto flex flex-col gap-2 scrollbar-thin">
                {agentLog.map((log, i) => {
                  const { className, icon } = getLogStyleAndIcon(log);
                  return (
                    <div key={i} className={`flex items-start gap-2 line-clamp-2 ${className}`}>
                      <span className="shrink-0 opacity-70">{icon}</span>
                      <span>{log}</span>
                    </div>
                  );
                })}
                <div ref={logEndRef} />
              </div>
            </div>
          )}

          {/* Results panel */}
          {result && !loading && (
            <div className="glass-card p-6 md:p-8 animate-fade-in space-y-6">
              {/* Summary Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-5">
                <div>
                  <span className="px-2.5 py-1 bg-success/15 border border-success/20 text-success rounded-lg text-xs font-semibold inline-flex items-center gap-1.5 mb-2">
                    <FileCheck className="w-3.5 h-3.5" />
                    Document Compiled Successfully
                  </span>
                  <h3 className="text-xl font-bold font-display text-white">{result.request}</h3>
                </div>

                <a 
                  href={getDownloadUrl(result.document_path)}
                  download
                  className="btn btn-primary shrink-0 self-start sm:self-center"
                >
                  <Download className="w-4 h-4" />
                  <span>Download DOCX file</span>
                </a>
              </div>

              {/* Highlights panel */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 bg-white/3 border border-white/5 rounded-xl">
                  <span className="text-xs text-slate-400 block mb-1">Execution Time</span>
                  <strong className="text-base text-white">{result.execution_time}</strong>
                </div>
                <div className="p-4 bg-white/3 border border-white/5 rounded-xl">
                  <span className="text-xs text-slate-400 block mb-1">Reflection Status</span>
                  <strong className={`text-base flex items-center gap-1.5 ${result.reflection_result?.status === 'PASS' ? 'text-success' : 'text-warning'}`}>
                    {result.reflection_result?.status || 'PASS'}
                  </strong>
                </div>
                <div className="p-4 bg-white/3 border border-white/5 rounded-xl">
                  <span className="text-xs text-slate-400 block mb-1">Total Sections</span>
                  <strong className="text-base text-white">
                    {result.sections_content ? Object.keys(result.sections_content).length : 0}
                  </strong>
                </div>
              </div>

              {/* Tabs for details */}
              <div className="flex border-b border-white/5">
                {[
                  { id: 'preview', label: 'Document Preview', icon: Eye },
                  { id: 'assumptions', label: 'Assumptions Made', icon: Layers },
                  { id: 'logs', label: 'Completed Agent Tasks', icon: Terminal }
                ].map(tab => {
                  const Icon = tab.icon;
                  const isActive = resultTab === tab.id;
                  return (
                    <button 
                      key={tab.id}
                      onClick={() => setResultTab(tab.id)}
                      className={`px-4 py-3 border-b-2 text-xs font-semibold font-display flex items-center gap-1.5 transition-all ${
                        isActive 
                          ? 'border-indigo-500 text-indigo-400' 
                          : 'border-transparent text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Tab Contents */}
              <div className="pt-2">
                {/* 1. Preview Tab */}
                {resultTab === 'preview' && (
                  <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    {/* Sections outline list */}
                    <div className="lg:col-span-1 border border-white/5 rounded-xl overflow-hidden divide-y divide-white/5 bg-slate-950/20">
                      {result.sections_content && Object.keys(result.sections_content).map(secName => (
                        <button 
                          key={secName}
                          onClick={() => setSelectedSection(secName)}
                          className={`w-full px-4 py-3 text-left text-xs font-semibold transition-all block truncate ${
                            selectedSection === secName 
                              ? 'bg-indigo-500/10 text-indigo-400 border-l-2 border-indigo-500' 
                              : 'text-slate-400 hover:text-slate-200 hover:bg-white/2'
                          }`}
                        >
                          {secName}
                        </button>
                      ))}
                    </div>

                    {/* Section body viewer */}
                    <div className="lg:col-span-3 border border-white/5 rounded-xl p-6 bg-slate-950/40 relative min-h-[300px]">
                      {selectedSection && result.sections_content ? (
                        <div className="markdown-preview animate-fade-in">
                          <h2 className="text-xl font-bold font-display text-indigo-300 border-b border-white/5 pb-2.5 mb-4">
                            {selectedSection}
                          </h2>
                          {renderMarkdown(result.sections_content[selectedSection])}
                        </div>
                      ) : (
                        <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                          Select a section from the outline to preview.
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 2. Assumptions Tab */}
                {resultTab === 'assumptions' && (
                  <div className="border border-white/5 rounded-xl p-5 bg-slate-950/20 space-y-3">
                    {result.assumptions && result.assumptions.length === 0 ? (
                      <div className="text-slate-500 text-sm py-4 text-center">No explicit assumptions defined.</div>
                    ) : (
                      result.assumptions && result.assumptions.map((ass, i) => (
                        <div key={i} className="flex gap-2.5 text-sm text-slate-300 items-start">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0 mt-2" />
                          <span>{ass}</span>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* 3. Completed Tasks / Logs Tab */}
                {resultTab === 'logs' && (
                  <div className="border border-white/5 rounded-xl p-5 bg-slate-950/20 font-mono text-[11px] text-slate-400 space-y-2 h-80 overflow-y-auto">
                    {result.completed_tasks && result.completed_tasks.map((task, i) => (
                      <div key={i} className="flex gap-2 items-start py-1 border-b border-white/2">
                        <CheckCircle className="w-3.5 h-3.5 text-success shrink-0 mt-0.5" />
                        <span className="text-slate-300">{task}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
