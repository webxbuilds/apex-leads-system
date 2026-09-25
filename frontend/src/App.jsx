import React, { useState, useEffect } from 'react'
import { LayoutDashboard, Users, FileText, Briefcase, BarChart3, Moon, Sun, Settings, LogOut, Menu, X, Sparkles } from 'lucide-react'
import DashboardView from './components/DashboardView'
import LeadsView from './components/LeadsView'
import ProposalsView from './components/ProposalsView'
import PortfoliosView from './components/PortfoliosView'
import AnalyticsView from './components/AnalyticsView'
import SettingsView from './components/SettingsView'
import LoginView from './components/LoginView'

const resolveInitialApiBase = () => {
  const saved = localStorage.getItem('apex_api_url')
  if (saved && saved.trim()) return saved.trim().replace(/\/$/, '')
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return "http://localhost:8000/api"
  }
  return 'https://apex-agency-backend.onrender.com/api'
}

export default function App() {
  const [session, setSession] = useState(() => {
    const saved = localStorage.getItem('apex_session')
    return saved ? JSON.parse(saved) : null
  })
  
  const [apiBase, setApiBase] = useState(resolveInitialApiBase)
  const [activeTab, setActiveTab] = useState('leads')
  const [darkMode, setDarkMode] = useState(true)
  const [notification, setNotification] = useState(null)
  const [leadsCount, setLeadsCount] = useState(0)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    if (!session) return

    // Sync leads count
    fetch(`${apiBase}/leads/`, {
      headers: { 'Authorization': `Bearer ${session.token}` }
    })
      .then(async res => {
        if (!res.ok) throw new Error('Unauthorised or expired token')
        const contentType = res.headers.get('content-type') || ''
        if (!contentType.includes('application/json')) throw new Error('Invalid server response')
        return res.json()
      })
      .then(data => {
        if (data && data.total !== undefined) setLeadsCount(data.total)
      })
      .catch(err => {
        console.error("Error connecting to backend: ", err)
        if (err.message.includes('Unauthorised')) {
          handleLogout()
        }
      })
  }, [activeTab, session, apiBase])

  const triggerAlert = (message, type = "success") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 5000)
  }

  const handleLogout = () => {
    localStorage.removeItem('apex_session')
    setSession(null)
    setActiveTab('dashboard')
  }

  // Auth barrier
  if (!session) {
    return <LoginView setSession={setSession} API_BASE={apiBase} setApiBase={setApiBase} />
  }

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'leads', label: 'Leads CRM', icon: Users, badge: leadsCount },
    { id: 'proposals', label: 'Proposals & Bills', icon: FileText },
    { id: 'portfolios', label: 'Demo Sites', icon: Briefcase },
    { id: 'analytics', label: 'Campaign Logs', icon: BarChart3 },
    { id: 'settings', label: 'System Settings', icon: Settings },
  ]

  return (
    <div className={`min-h-screen font-sans ${darkMode ? 'bg-zinc-950 text-zinc-100' : 'bg-zinc-50 text-zinc-800'}`}>
      
      {/* Top Banner alert */}
      {notification && (
        <div className={`fixed top-4 right-4 left-4 sm:left-auto z-50 flex items-center gap-3 p-4 rounded-xl border shadow-2xl transition-all duration-300 transform translate-y-0 ${
          notification.type === 'success' 
            ? 'bg-emerald-950/90 border-emerald-700 text-emerald-200' 
            : 'bg-red-950/90 border-red-700 text-red-200'
        }`}>
          <span className="text-xs sm:text-sm font-semibold">{notification.message}</span>
        </div>
      )}

      {/* Main Container */}
      <div className="flex h-screen overflow-hidden relative">
        
        {/* Mobile Backdrop Overlay */}
        {mobileMenuOpen && (
          <div 
            onClick={() => setMobileMenuOpen(false)}
            className="fixed inset-0 bg-black/75 backdrop-blur-sm z-40 md:hidden transition-opacity"
          />
        )}

        {/* Sidebar (Desktop Permanent + Mobile Slide-out Drawer) */}
        <aside className={`fixed md:relative top-0 bottom-0 left-0 z-50 w-72 md:w-64 border-r flex flex-col justify-between shrink-0 transition-transform duration-300 ease-in-out ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        } ${darkMode ? 'bg-zinc-950 md:bg-zinc-900/40 border-zinc-800/80' : 'bg-white border-zinc-200'}`}>
          <div>
            {/* Header / Logo */}
            <div className="p-5 md:p-6 flex items-center justify-between border-b border-zinc-850">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
                  ⚡
                </div>
                <div>
                  <span className="font-extrabold text-white text-base tracking-tight block">ApexWeb System</span>
                  <span className="text-[10px] text-indigo-400 font-bold tracking-wider uppercase">Operating OS</span>
                </div>
              </div>

              {/* Close button on mobile */}
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="p-1.5 text-zinc-400 hover:text-white rounded-lg md:hidden"
              >
                <X size={20} />
              </button>
            </div>

            {/* User Profile Card inside Sidebar */}
            <div className="p-3.5 mx-4 my-3 bg-zinc-950/60 border border-zinc-850 rounded-2xl flex items-center justify-between">
              <div className="min-w-0">
                <p className="text-[11px] font-bold text-white truncate">{session.fullName}</p>
                <p className="text-[9px] text-indigo-400 font-semibold uppercase mt-0.5">{session.role}</p>
              </div>
              <button 
                onClick={handleLogout} 
                className="p-2 text-zinc-500 hover:text-red-400 hover:bg-red-950/20 rounded-lg transition"
                title="Logout Session"
              >
                <LogOut size={14} />
              </button>
            </div>

            {/* Nav Menu */}
            <nav className="p-4 space-y-1.5">
              {navItems.map(item => {
                const Icon = item.icon
                const isActive = activeTab === item.id
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveTab(item.id)
                      setMobileMenuOpen(false)
                    }}
                    className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-xs font-semibold tracking-wide transition-all ${
                      isActive 
                        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/10' 
                        : darkMode 
                          ? 'text-zinc-400 hover:bg-zinc-800/50 hover:text-white' 
                          : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-zinc-400'}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge !== undefined && item.badge > 0 && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {item.badge}
                      </span>
                    )}
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Footer Controls */}
          <div className="p-4 border-t border-zinc-800/60 flex items-center justify-between gap-4">
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`p-2.5 rounded-xl border transition ${
                darkMode ? 'bg-zinc-900 border-zinc-800 hover:bg-zinc-800 text-zinc-400 hover:text-white' : 'bg-zinc-100 border-zinc-200 hover:bg-zinc-200 text-zinc-600 hover:text-zinc-950'
              }`}
              title="Toggle Theme"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <div className="text-left flex-1 min-w-0">
              <p className="text-[10px] text-zinc-500 font-bold block">Status</p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-[11px] font-bold text-zinc-300 truncate">System Online</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Content Pane */}
        <main className="flex-1 flex flex-col min-w-0 overflow-y-auto no-scrollbar pb-20 md:pb-6">
          {/* Responsive Header Panel */}
          <header className={`px-4 sm:px-6 md:px-8 py-3.5 md:py-4 border-b flex items-center justify-between shrink-0 sticky top-0 z-30 backdrop-blur-md ${
            darkMode ? 'bg-zinc-950/80 border-zinc-800/50' : 'bg-white/80 border-zinc-200'
          }`}>
            <div className="flex items-center gap-3">
              {/* Hamburger Button for mobile */}
              <button
                onClick={() => setMobileMenuOpen(true)}
                className="p-2 -ml-1 text-zinc-400 hover:text-white hover:bg-zinc-800/60 rounded-xl md:hidden transition"
                title="Open Menu"
              >
                <Menu size={20} />
              </button>

              <div>
                <h2 className="text-base sm:text-lg font-bold tracking-tight text-white leading-tight">
                  {activeTab === 'leads' ? 'Leads CRM' : (activeTab.charAt(0).toUpperCase() + activeTab.slice(1))}
                </h2>
                <p className="text-[10px] text-zinc-400 hidden sm:block">Real-time automation monitoring & B2B growth console</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1 bg-zinc-900/90 border border-zinc-800 rounded-xl shadow-inner">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                <span className="text-[9px] sm:text-[10px] font-bold text-zinc-300 tracking-wider">GEMINI AI</span>
              </div>
            </div>
          </header>

          {/* Tab Render Switcher */}
          <div className="flex-1 p-3.5 sm:p-6 md:p-8">
            {activeTab === 'dashboard' && <DashboardView API_BASE={apiBase} activeTab={activeTab} setActiveTab={setActiveTab} session={session} />}
            {activeTab === 'leads' && <LeadsView API_BASE={apiBase} triggerAlert={triggerAlert} session={session} />}
            {activeTab === 'proposals' && <ProposalsView API_BASE={apiBase} triggerAlert={triggerAlert} session={session} />}
            {activeTab === 'portfolios' && <PortfoliosView API_BASE={apiBase} triggerAlert={triggerAlert} session={session} />}
            {activeTab === 'analytics' && <AnalyticsView API_BASE={apiBase} session={session} />}
            {activeTab === 'settings' && <SettingsView API_BASE={apiBase} setApiBase={setApiBase} session={session} />}
          </div>
        </main>

        {/* Mobile Bottom Navigation Bar */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-zinc-950/95 backdrop-blur-xl border-t border-zinc-800/80 px-2 py-2 flex justify-around items-center shadow-2xl">
          {navItems.map(item => {
            const Icon = item.icon
            const isActive = activeTab === item.id
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex flex-col items-center gap-1 px-2.5 py-1 rounded-xl transition ${
                  isActive ? 'text-indigo-400' : 'text-zinc-500 hover:text-zinc-300'
                }`}
              >
                <div className="relative">
                  <Icon size={18} />
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="absolute -top-1 -right-2 w-3.5 h-3.5 rounded-full bg-indigo-600 text-white text-[8px] font-bold flex items-center justify-center">
                      {item.badge > 99 ? '99+' : item.badge}
                    </span>
                  )}
                </div>
                <span className="text-[9px] font-medium tracking-tight">
                  {item.id === 'dashboard' ? 'Home' : item.id === 'leads' ? 'Leads' : item.id === 'proposals' ? 'Proposals' : item.id === 'portfolios' ? 'Demos' : item.id === 'analytics' ? 'Logs' : 'Settings'}
                </span>
              </button>
            )
          })}
        </nav>

      </div>
    </div>
  )
}
