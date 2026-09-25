import React, { useState, useEffect } from 'react'
import { Save, ShieldAlert, KeyRound, Mail, Settings, Palette } from 'lucide-react'

export default function SettingsView({ API_BASE, setApiBase, session }) {
  const [companyName, setCompanyName] = useState('')
  const [companyEmail, setCompanyEmail] = useState('')
  const [smtpHost, setSmtpHost] = useState('')
  const [smtpPort, setSmtpPort] = useState(587)
  const [smtpUser, setSmtpUser] = useState('')
  const [smtpPass, setSmtpPass] = useState('')
  const [geminiApiKey, setGeminiApiKey] = useState('')
  const [n8nWebhookUrl, setN8nWebhookUrl] = useState('')
  const [logoUrl, setLogoUrl] = useState('')
  const [brandingColor, setBrandingColor] = useState('#6366f1')
  const [backendApiUrl, setBackendApiUrl] = useState(API_BASE || '')

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    fetch(`${API_BASE}/settings/`, {
      headers: { 'Authorization': `Bearer ${session?.token}` }
    })
      .then(res => res.json())
      .then(data => {
        setCompanyName(data.company_name || '')
        setCompanyEmail(data.company_email || '')
        setSmtpHost(data.smtp_host || '')
        setSmtpPort(data.smtp_port || 587)
        setSmtpUser(data.smtp_user || '')
        setSmtpPass(data.smtp_pass || '')
        setGeminiApiKey(data.gemini_api_key || '')
        setN8nWebhookUrl(data.n8n_webhook_url || '')
        setLogoUrl(data.logo_url || '')
        setBrandingColor(data.branding_color || '#6366f1')
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load settings:', err)
        setLoading(false)
      })
  }, [API_BASE, session])

  const handleSave = (e) => {
    e.preventDefault()
    setSaving(true)
    setNotice('')

    if (backendApiUrl) {
      let cleanUrl = backendApiUrl.trim().replace(/\/$/, '')
      if (!cleanUrl.endsWith('/api') && !cleanUrl.includes('/api/')) {
        cleanUrl = `${cleanUrl}/api`
      }
      localStorage.setItem('apex_api_url', cleanUrl)
      if (setApiBase) setApiBase(cleanUrl)
    }

    fetch(`${API_BASE}/settings/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session?.token}`
      },
      body: JSON.stringify({
        company_name: companyName,
        company_email: companyEmail,
        smtp_host: smtpHost,
        smtp_port: parseInt(smtpPort),
        smtp_user: smtpUser,
        smtp_pass: smtpPass,
        gemini_api_key: geminiApiKey,
        n8n_webhook_url: n8nWebhookUrl,
        logo_url: logoUrl,
        branding_color: brandingColor
      })
    })
      .then(async res => {
        if (!res.ok) {
          const errData = await res.json()
          throw new Error(errData.detail || 'Access restricted. Administrator role required.')
        }
        return res.json()
      })
      .then(() => {
        setNotice('✅ Settings saved successfully.')
        setSaving(false)
      })
      .catch(err => {
        setNotice(`❌ Error: ${err.message}`)
        setSaving(false)
      })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-4xl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight uppercase">System Settings</h2>
          <p className="text-[10px] text-zinc-500 mt-1 uppercase tracking-wider">Configure API Keys, SMTP, integrations and company branding parameters.</p>
        </div>
      </div>

      {notice && (
        <div className={`p-4 rounded-xl text-xs ${notice.includes('successfully') ? 'bg-emerald-950/40 border border-emerald-905/30 text-emerald-400' : 'bg-red-950/40 border border-red-900/30 text-red-400'}`}>
          {notice}
        </div>
      )}

      {session?.role !== 'Admin' && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-900/30 text-amber-400 text-xs flex gap-3 items-center">
          <ShieldAlert size={16} />
          <span>Restricted Mode: Standard users can view configurations. Making modifications requires Administrator role.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Company Profile */}
        <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 space-y-4">
          <h3 className="text-xs font-bold text-white tracking-wide uppercase flex items-center gap-2">
            <Settings size={14} className="text-indigo-400" />
            Company Branding Profile
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5">Agency Name</label>
              <input
                type="text"
                value={companyName}
                onChange={e => setCompanyName(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
                placeholder="e.g. Apex Web Solutions"
              />
            </div>
            <div>
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5">Primary Contact Email</label>
              <input
                type="email"
                value={companyEmail}
                onChange={e => setCompanyEmail(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
                placeholder="e.g. hello@company.com"
              />
            </div>
            <div>
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5">Brand Logo URL</label>
              <input
                type="text"
                value={logoUrl}
                onChange={e => setLogoUrl(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
                placeholder="https://example.com/logo.png"
              />
            </div>
            <div>
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5 flex justify-between items-center">
                <span>Interface Highlight Color</span>
                <span className="text-[10px]" style={{ color: brandingColor }}>{brandingColor}</span>
              </label>
              <div className="flex gap-3">
                <input
                  type="color"
                  value={brandingColor}
                  onChange={e => setBrandingColor(e.target.value)}
                  className="w-12 h-10 bg-transparent border-0 cursor-pointer focus:outline-none"
                />
                <input
                  type="text"
                  value={brandingColor}
                  onChange={e => setBrandingColor(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* API keys */}
        <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 space-y-4">
          <h3 className="text-xs font-bold text-white tracking-wide uppercase flex items-center gap-2">
            <KeyRound size={14} className="text-indigo-400" />
            AI & Automation APIs Keys
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5">Backend API Server Endpoint URL</label>
              <input
                type="text"
                value={backendApiUrl}
                onChange={e => setBackendApiUrl(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                placeholder="https://your-api.onrender.com/api"
              />
              <p className="text-[10px] text-zinc-500 mt-1">
                Used by the client application to communicate with your FastAPI backend.
              </p>
            </div>
            <div>
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5">Gemini Free API Key</label>
              <input
                type="password"
                value={geminiApiKey}
                onChange={e => setGeminiApiKey(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                placeholder="AIzaSy..."
              />
            </div>
            <div>
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5">n8n Lead Push Webhook URL</label>
              <input
                type="text"
                value={n8nWebhookUrl}
                onChange={e => setN8nWebhookUrl(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
                placeholder="http://localhost:5678/webhook/..."
              />
            </div>
          </div>
        </div>

        {/* SMTP Mail settings */}
        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 space-y-4">
          <h3 className="text-xs font-bold text-white tracking-wide uppercase flex items-center gap-2">
            <Mail size={14} className="text-indigo-400" />
            SMTP Outbound Email Relay
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5">SMTP Host Server</label>
              <input
                type="text"
                value={smtpHost}
                onChange={e => setSmtpHost(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
                placeholder="smtp.gmail.com"
              />
            </div>
            <div>
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5">SMTP Port</label>
              <input
                type="number"
                value={smtpPort}
                onChange={e => setSmtpPort(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5">SMTP Username</label>
              <input
                type="text"
                value={smtpUser}
                onChange={e => setSmtpUser(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
                placeholder="email@gmail.com"
              />
            </div>
            <div>
              <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1.5">SMTP Password</label>
              <input
                type="password"
                value={smtpPass}
                onChange={e => setSmtpPass(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-805/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
                placeholder="••••••••••••"
              />
            </div>
          </div>
        </div>

        {session?.role === 'Admin' && (
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold rounded-xl text-xs uppercase tracking-wider transition shadow-lg shadow-indigo-600/20 active:scale-95"
            >
              <Save size={14} />
              {saving ? 'Saving Configs...' : 'Save Settings'}
            </button>
          </div>
        )}
      </form>
    </div>
  )
}
