import React, { useState } from 'react'
import { Server, CheckCircle2, AlertCircle, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'

export default function LoginView({ setSession, API_BASE, setApiBase }) {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState('Sales')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Server URL Configuration state
  const [showServerConfig, setShowServerConfig] = useState(false)
  const [customApiUrl, setCustomApiUrl] = useState(API_BASE || '')
  const [testingServer, setTestingServer] = useState(false)
  const [serverStatus, setServerStatus] = useState(null) // { success: boolean, message: string }

  const handleSaveApiUrl = (e) => {
    e?.preventDefault()
    let cleanUrl = customApiUrl.trim().replace(/\/$/, '')
    if (!cleanUrl.endsWith('/api') && !cleanUrl.includes('/api/')) {
      cleanUrl = `${cleanUrl}/api`
    }
    localStorage.setItem('apex_api_url', cleanUrl)
    if (setApiBase) setApiBase(cleanUrl)
    setServerStatus({ success: true, message: `Saved! Connecting to: ${cleanUrl}` })
    setError('')
  }

  const handleTestConnection = async () => {
    setTestingServer(true)
    setServerStatus(null)
    let testUrl = customApiUrl.trim().replace(/\/$/, '')
    const baseRoot = testUrl.replace(/\/api\/?$/, '')

    try {
      const res = await fetch(`${baseRoot}/`, { method: 'GET' })
      const contentType = res.headers.get('content-type') || ''
      if (contentType.includes('application/json')) {
        const data = await res.json()
        setServerStatus({
          success: true,
          message: `Connected! Service: ${data.service || 'Apex API Online'}`
        })
      } else {
        const text = await res.text()
        if (text.includes('<!DOCTYPE') || text.includes('<html')) {
          setServerStatus({
            success: false,
            message: `Returned HTML page instead of API JSON. Ensure your backend URL is correct.`
          })
        } else {
          setServerStatus({ success: true, message: `Server reached (Status ${res.status})` })
        }
      }
    } catch (err) {
      setServerStatus({
        success: false,
        message: `Connection failed: ${err.message}. Check if your backend server is running.`
      })
    } finally {
      setTestingServer(false)
    }
  }

  const parseResponseSafe = async (res) => {
    const contentType = res.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      return await res.json()
    }
    const text = await res.text()
    if (text.startsWith('<!DOCTYPE') || text.includes('<html')) {
      throw new Error(
        `Backend API server not found at "${API_BASE}". The server returned a 404 HTML page. Please configure your live backend API URL below.`
      )
    }
    try {
      return JSON.parse(text)
    } catch {
      throw new Error(text || `Server returned HTTP ${res.status}`)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    if (isRegister) {
      // Register request
      fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName, role })
      })
        .then(async (res) => {
          const data = await parseResponseSafe(res)
          if (!res.ok) {
            throw new Error(data.detail || 'Registration failed.')
          }
          return data
        })
        .then(() => {
          // Registration success, toggle to login immediately
          setIsRegister(false)
          setError('Account registered successfully! Please login.')
          setLoading(false)
        })
        .catch((err) => {
          setError(err.message || 'Registration failed.')
          setShowServerConfig(true)
          setLoading(false)
        })
    } else {
      // Login request (requires URLencoded parameters for OAuth2 password form)
      const formParams = new URLSearchParams()
      formParams.append('username', email)
      formParams.append('password', password)

      fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formParams
      })
        .then(async (res) => {
          const data = await parseResponseSafe(res)
          if (!res.ok) {
            throw new Error(data.detail || 'Login failed. Please check credentials.')
          }
          return data
        })
        .then((data) => {
          // Save JWT session details
          const session = {
            token: data.access_token,
            role: data.role,
            fullName: data.full_name,
            email: email
          }
          localStorage.setItem('apex_session', JSON.stringify(session))
          setSession(session)
          setLoading(false)
        })
        .catch((err) => {
          setError(err.message || 'Login failed. Please verify credentials.')
          if (err.message.includes('Backend API server') || err.message.includes('<!DOCTYPE') || err.message.includes('Failed to fetch')) {
            setShowServerConfig(true)
          }
          setLoading(false)
        })
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 p-4 sm:p-6 relative overflow-hidden select-none">
      {/* Background glowing gradients */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-fuchsia-500/10 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-md p-6 sm:p-8 rounded-3xl bg-zinc-900/60 backdrop-blur-xl border border-zinc-800/80 shadow-2xl relative z-10">
        <div className="text-center mb-6 sm:mb-8">
          <span className="text-3xl sm:text-4xl">⚡</span>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight mt-3 sm:mt-4">APEX CRM OPERATING OS</h2>
          <p className="text-xs text-zinc-400 mt-1.5">Scale and automate your agency outreach pipelines</p>
        </div>

        {error && (
          <div className={`p-4 rounded-xl text-xs mb-5 leading-relaxed ${
            error.includes('successfully') 
              ? 'bg-emerald-950/50 border border-emerald-800 text-emerald-300' 
              : 'bg-red-950/60 border border-red-800/80 text-red-300'
          }`}>
            <div className="flex items-start gap-2">
              <AlertCircle size={15} className="shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">{error}</p>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <>
              <div>
                <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 focus:border-indigo-500 text-sm rounded-xl p-3 text-white focus:outline-none transition shadow-inner"
                  placeholder="Sujal"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">Assign System Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 focus:border-indigo-500 text-sm rounded-xl p-3 text-white focus:outline-none transition"
                >
                  <option value="Admin">Administrator</option>
                  <option value="Sales">Sales Account Executive</option>
                  <option value="Auditor">Web Security Auditor</option>
                </select>
              </div>
            </>
          )}

          <div>
            <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 focus:border-indigo-500 text-sm rounded-xl p-3 text-white focus:outline-none transition shadow-inner"
              placeholder="admin@agency.com"
            />
          </div>

          <div>
            <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">Security Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 focus:border-indigo-500 text-sm rounded-xl p-3 text-white focus:outline-none transition shadow-inner"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold rounded-xl text-xs tracking-wider uppercase transition shadow-lg shadow-indigo-600/25 mt-4 active:scale-95"
          >
            {loading ? 'Processing System Check...' : isRegister ? 'Register Account' : 'Authenticate Session'}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-zinc-500">
          <span className="mr-1">
            {isRegister ? 'Already registered to the hub?' : 'New team representative?'}
          </span>
          <button
            onClick={() => {
              setIsRegister(!isRegister)
              setError('')
            }}
            className="text-indigo-400 font-bold hover:underline"
          >
            {isRegister ? 'Sign In Instead' : 'Register Here'}
          </button>
        </div>

        {/* Server Endpoint Configuration Drawer */}
        <div className="mt-6 pt-4 border-t border-zinc-800/60">
          <button
            type="button"
            onClick={() => setShowServerConfig(!showServerConfig)}
            className="w-full flex items-center justify-between text-[11px] text-zinc-400 hover:text-zinc-200 transition"
          >
            <span className="flex items-center gap-1.5 font-medium">
              <Server size={13} className="text-indigo-400" />
              <span>Backend API Server Settings</span>
            </span>
            {showServerConfig ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>

          {showServerConfig && (
            <div className="mt-3 p-3.5 bg-zinc-950/80 border border-zinc-800 rounded-2xl space-y-3 animate-in fade-in duration-150">
              <div>
                <label className="block text-[9px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
                  Live Backend API Endpoint URL
                </label>
                <input
                  type="text"
                  value={customApiUrl}
                  onChange={(e) => setCustomApiUrl(e.target.value)}
                  placeholder="https://your-api.onrender.com/api"
                  className="w-full bg-zinc-900 border border-zinc-700/80 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                />
                <p className="text-[10px] text-zinc-500 mt-1">
                  Enter your hosted backend URL (e.g. Render, Railway, or VPS).
                </p>
              </div>

              {serverStatus && (
                <div className={`p-2.5 rounded-lg text-[10px] flex items-start gap-1.5 ${
                  serverStatus.success 
                    ? 'bg-emerald-950/60 border border-emerald-800 text-emerald-300' 
                    : 'bg-red-950/60 border border-red-800 text-red-300'
                }`}>
                  {serverStatus.success ? <CheckCircle2 size={13} className="shrink-0 mt-0.5" /> : <AlertCircle size={13} className="shrink-0 mt-0.5" />}
                  <span>{serverStatus.message}</span>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testingServer}
                  className="flex-1 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 font-semibold text-xs rounded-lg flex items-center justify-center gap-1.5 transition active:scale-95"
                >
                  <RefreshCw size={12} className={testingServer ? 'animate-spin' : ''} />
                  <span>{testingServer ? 'Pinging...' : 'Test Connection'}</span>
                </button>
                <button
                  type="button"
                  onClick={handleSaveApiUrl}
                  className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-lg transition active:scale-95 shadow-md"
                >
                  Save & Connect
                </button>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
