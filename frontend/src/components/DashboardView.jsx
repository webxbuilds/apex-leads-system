import React, { useState, useEffect } from 'react'
import { Bar, Line, Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend } from 'chart.js'
import { Users, Target, CircleDollarSign, Send, ArrowUpRight, CheckCircle2, Clock, Calendar, CheckSquare, Plus, Trash2, RefreshCw, Flame, Sparkles } from 'lucide-react'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend)

export default function DashboardView({ API_BASE, setActiveTab, session }) {
  const [data, setData] = useState(null)
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  // Task creation states
  const [showTaskForm, setShowTaskForm] = useState(false)
  const [taskTitle, setTaskTitle] = useState('')
  const [taskDesc, setTaskDesc] = useState('')
  const [taskDue, setTaskDue] = useState('')
  const [taskLeadId, setTaskLeadId] = useState('')
  const [leadsList, setLeadsList] = useState([])

  const loadData = () => {
    setLoading(true)
    setError(false)
    
    const headers = { 'Authorization': `Bearer ${session?.token}` }
    
    const fetchDashboard = fetch(`${API_BASE}/analytics/dashboard`, { headers }).then(res => res.json())
    const fetchTasks = fetch(`${API_BASE}/tasks/`, { headers }).then(res => res.json())
    const fetchLeads = fetch(`${API_BASE}/leads/?limit=100`, { headers }).then(res => res.json())

    Promise.all([fetchDashboard, fetchTasks, fetchLeads])
      .then(([dbData, tasksData, leadsData]) => {
        setData(dbData)
        setTasks(tasksData)
        setLeadsList(leadsData.leads || [])
        setLoading(false)
      })
      .catch(err => {
        console.error("Error loading dashboard data: ", err)
        setError(true)
        setLoading(false)
      })
  }

  useEffect(() => {
    loadData()
  }, [API_BASE, session])

  const handleToggleTask = (taskId, currentStatus) => {
    const nextStatus = currentStatus === 'Completed' ? 'Pending' : 'Completed'
    
    fetch(`${API_BASE}/tasks/${taskId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session?.token}`
      },
      body: JSON.stringify({ status: nextStatus })
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to update task status')
        // Refresh local tasks list
        setTasks(tasks.map(t => t.id === taskId ? { ...t, status: nextStatus } : t))
      })
      .catch(err => console.error(err))
  }

  const handleDeleteTask = (taskId) => {
    fetch(`${API_BASE}/tasks/${taskId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${session?.token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to delete task')
        setTasks(tasks.filter(t => t.id !== taskId))
      })
      .catch(err => console.error(err))
  }

  const handleCreateTask = (e) => {
    e.preventDefault()
    if (!taskTitle || !taskDue) return

    fetch(`${API_BASE}/tasks/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session?.token}`
      },
      body: JSON.stringify({
        title: taskTitle,
        description: taskDesc,
        due_date: new Date(taskDue).toISOString(),
        lead_id: taskLeadId ? parseInt(taskLeadId) : null
      })
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to create task')
        return res.json()
      })
      .then(() => {
        // Clear fields & reload
        setTaskTitle('')
        setTaskDesc('')
        setTaskDue('')
        setTaskLeadId('')
        setShowTaskForm(false)
        loadData()
      })
      .catch(err => console.error(err))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  const stats = data?.kpis || {
    total_leads: 0,
    conversion_rate: 0,
    actual_revenue: 0,
    projected_value: 0,
    won_clients: 0
  }

  const trendData = data?.leads_trend || []
  const pipeline = data?.pipeline || data?.pipeline_stats || {}
  const nichesChart = data?.niches_chart || []

  const trendChartData = {
    labels: trendData.map(t => t.date),
    datasets: [
      {
        label: 'Leads Acquired',
        data: trendData.map(t => t.count),
        borderColor: 'rgb(99, 102, 241)',
        backgroundColor: 'rgba(99, 102, 241, 0.15)',
        tension: 0.4,
        fill: true,
        borderWidth: 2,
        pointRadius: 3
      }
    ]
  }

  const pipelineChartData = {
    labels: Object.keys(pipeline),
    datasets: [
      {
        data: Object.values(pipeline),
        backgroundColor: [
          'rgba(99, 102, 241, 0.85)',
          'rgba(168, 85, 247, 0.85)',
          'rgba(236, 72, 153, 0.85)',
          'rgba(244, 63, 94, 0.85)',
          'rgba(234, 179, 8, 0.85)',
          'rgba(34, 197, 94, 0.85)',
          'rgba(107, 114, 128, 0.85)'
        ],
        borderWidth: 0
      }
    ]
  }

  const nichesChartData = {
    labels: nichesChart.map(n => n.niche),
    datasets: [
      {
        label: 'Avg Probability of Close (%)',
        data: nichesChart.map(n => n.success_probability),
        backgroundColor: 'rgba(217, 70, 239, 0.85)',
        borderWidth: 0,
        borderRadius: 8
      }
    ]
  }

  const noWebsiteLeads = leadsList.filter(l => !l.has_website || !l.website || l.website === "Not Publicly Available" || l.website === "none")

  return (
    <div className="space-y-6">
      {/* Top Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Agency Command Center</h1>
          <p className="text-xs text-zinc-400 mt-1">Real-time business discovery, qualification, and sales intelligence.</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-[#101524] hover:bg-[#182035] hover:text-white border border-[#1e273a] text-zinc-200 text-xs font-semibold rounded-lg shadow-sm transition active:scale-95"
            title="Refresh dashboard metrics and leads"
          >
            <RefreshCw size={13} className={`${loading ? "animate-spin text-indigo-400" : "text-indigo-400"}`} />
            <span>{loading ? "Refreshing..." : "Refresh Dashboard"}</span>
          </button>
          
          <button
            onClick={() => setActiveTab('leads')}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-md transition active:scale-95"
          >
            <span>Open Leads CRM →</span>
          </button>
        </div>
      </div>

      {/* High-Converting Missing Website Opportunity Banner */}
      {noWebsiteLeads.length > 0 && (
        <div className="p-4 bg-gradient-to-r from-[#291708] via-[#1a1122] to-[#0f1424] border border-amber-500/60 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-lg shadow-amber-950/20">
          <div className="flex items-start sm:items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400 flex items-center justify-center shrink-0">
              <Flame size={20} className="animate-pulse" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <span>{noWebsiteLeads.length} Businesses Found Without A Website</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500 text-black uppercase">High Intent</span>
              </h4>
              <p className="text-xs text-zinc-400 mt-0.5">
                These prospects have active Google Maps profiles & customer reviews but zero website. They have high conversion probability when pitched with an instant prototype.
              </p>
            </div>
          </div>
          <button
            onClick={() => setActiveTab('leads')}
            className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black font-bold text-xs rounded-xl shadow-md transition shrink-0 active:scale-95"
          >
            Pitch Website Leads ({noWebsiteLeads.length}) →
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-amber-950/40 border border-amber-900 rounded-2xl flex items-center justify-between text-xs text-amber-400">
          <span>⚠️ Connection to FastAPI backend offline. Displaying local demo metrics.</span>
          <button onClick={loadData} className="underline font-bold hover:text-amber-300">Retry Connection</button>
        </div>
      )}

      {/* Overview stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        
        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 flex justify-between items-start">
          <div>
            <span className="text-[10px] font-bold text-zinc-500 tracking-wider uppercase">Active Pipeline Leads</span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-white mt-1.5">{stats.total_leads || 0}</h3>
            <p className="text-[10px] text-zinc-400 mt-2 flex items-center gap-1">
              <span className="text-amber-400 font-bold">{stats.archived_leads || 0} Leads in ARC Queue</span>
            </p>
          </div>
          <div className="p-2.5 sm:p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Users className="w-4 sm:w-5 h-4 sm:h-5" />
          </div>
        </div>

        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 flex justify-between items-start">
          <div>
            <span className="text-[10px] font-bold text-zinc-500 tracking-wider uppercase">Conversion Rate</span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-white mt-1.5">{stats.conversion_rate}%</h3>
            <p className="text-[10px] text-zinc-400 mt-2 flex items-center gap-1">
              <span className="text-emerald-400 font-bold">+{stats.won_clients} Closed</span> clients total
            </p>
          </div>
          <div className="p-2.5 sm:p-3 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Target className="w-4 sm:w-5 h-4 sm:h-5" />
          </div>
        </div>

        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 flex justify-between items-start">
          <div>
            <span className="text-[10px] font-bold text-zinc-500 tracking-wider uppercase">Actual Revenue</span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-emerald-400 mt-1.5">₹{(stats.actual_revenue || 0).toLocaleString('en-IN')}</h3>
            <p className="text-[10px] text-zinc-400 mt-2 flex items-center gap-1">
              Based on signed contracts
            </p>
          </div>
          <div className="p-2.5 sm:p-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CircleDollarSign className="w-4 sm:w-5 h-4 sm:h-5" />
          </div>
        </div>

        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 flex justify-between items-start">
          <div>
            <span className="text-[10px] font-bold text-zinc-500 tracking-wider uppercase">Projected Value</span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-indigo-400 mt-1.5">₹{(stats.projected_revenue || stats.projected_value || 0).toLocaleString('en-IN')}</h3>
            <p className="text-[10px] text-zinc-400 mt-2 flex items-center gap-1">
              Pipeline estimations
            </p>
          </div>
          <div className="p-2.5 sm:p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Send className="w-4 sm:w-5 h-4 sm:h-5" />
          </div>
        </div>

      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Trend line chart */}
        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 lg:col-span-2 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-white tracking-wide uppercase">Leads Acquisition Trend</h4>
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Number of new leads imported or crawled over time</span>
          </div>
          <div className="h-64">
            <Line 
              data={trendChartData} 
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                  x: { grid: { display: false }, ticks: { color: '#71717a', font: { size: 10 } } },
                  y: { grid: { color: '#1e1e24' }, ticks: { color: '#71717a', font: { size: 10 } } }
                }
              }}
            />
          </div>
        </div>

        {/* Pipeline Distribution Chart */}
        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-white tracking-wide uppercase">CRM Pipeline Funnel</h4>
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Distribution of leads across sales stages</span>
          </div>
          <div className="h-64 flex items-center justify-center">
            <Doughnut 
              data={pipelineChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'right', labels: { color: '#a1a1aa', font: { size: 10 } } } }
              }}
            />
          </div>
        </div>

      </div>

      {/* Niches Success and Quick Launcher */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Niche success chart */}
        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-white tracking-wide uppercase">Niche Close Probability</h4>
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Categories with highest customer alignment</span>
          </div>
          <div className="h-64">
            <Bar
              data={nichesChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                  x: { grid: { display: false }, ticks: { color: '#71717a', font: { size: 10 } } },
                  y: { grid: { color: '#1e1e24' }, ticks: { color: '#71717a', font: { size: 10 } } }
                }
              }}
            />
          </div>
        </div>

        {/* Quick automation actions */}
        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 lg:col-span-2 flex flex-col justify-between">
          <div className="space-y-2">
            <h4 className="text-sm font-bold text-white tracking-wide uppercase">Automation Quick Launcher</h4>
            <p className="text-xs text-zinc-400">Apex System uses integrated background scrapers and analyzer services. Launch tasks instantly or configure schedules.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mt-6">
            <button onClick={() => setActiveTab('leads')} className="p-3.5 sm:p-4 rounded-xl bg-zinc-950 border border-zinc-800 text-left hover:border-indigo-500 transition">
              <span className="text-xs font-bold text-white block">Scrape New Leads</span>
              <span className="text-[10px] text-zinc-500 mt-1 block">Google Maps, Justdial crawler launcher</span>
            </button>
            <button onClick={() => setActiveTab('proposals')} className="p-3.5 sm:p-4 rounded-xl bg-zinc-950 border border-zinc-800 text-left hover:border-indigo-500 transition">
              <span className="text-xs font-bold text-white block">Draft Proposals</span>
              <span className="text-[10px] text-zinc-500 mt-1 block">Generate professional bills and contracts</span>
            </button>
            <button onClick={() => setActiveTab('portfolios')} className="p-3.5 sm:p-4 rounded-xl bg-zinc-950 border border-zinc-800 text-left hover:border-indigo-500 transition">
              <span className="text-xs font-bold text-white block">Portfolio Templates</span>
              <span className="text-[10px] text-zinc-500 mt-1 block">Custom visual demo prototypes templates</span>
            </button>
            <button onClick={() => setActiveTab('analytics')} className="p-3.5 sm:p-4 rounded-xl bg-zinc-950 border border-zinc-800 text-left hover:border-indigo-500 transition">
              <span className="text-xs font-bold text-white block">Outreach Campaign Analytics</span>
              <span className="text-[10px] text-zinc-500 mt-1 block">Track direct email, WhatsApp delivery logs</span>
            </button>
          </div>
        </div>

      </div>

      {/* CRM Calendar and Actionable Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Actionable Tasks List */}
        <div className="p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 md:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h4 className="text-sm font-bold text-white tracking-wide uppercase">Scheduled Pipeline Tasks</h4>
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Active reminders for follow-ups and meetings</span>
            </div>
            <button 
              onClick={() => setShowTaskForm(!showTaskForm)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-[10px] uppercase tracking-wider transition"
            >
              <Plus size={12} />
              {showTaskForm ? 'Cancel' : 'New Task'}
            </button>
          </div>

          {showTaskForm && (
            <form onSubmit={handleCreateTask} className="p-4 bg-zinc-950/60 border border-zinc-805/50 rounded-xl space-y-3 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1">Task Title</label>
                  <input 
                    type="text" 
                    required 
                    value={taskTitle} 
                    onChange={e => setTaskTitle(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white" 
                    placeholder="e.g. Call client back" 
                  />
                </div>
                <div>
                  <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1">Due Date & Time</label>
                  <input 
                    type="datetime-local" 
                    required 
                    value={taskDue} 
                    onChange={e => setTaskDue(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white" 
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1">Link Lead (Optional)</label>
                  <select
                    value={taskLeadId}
                    onChange={e => setTaskLeadId(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white"
                  >
                    <option value="">-- Select Lead --</option>
                    {leadsList.map(l => (
                      <option key={l.id} value={l.id}>{l.business_name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[9px] font-bold text-zinc-500 uppercase mb-1">Notes</label>
                  <input 
                    type="text" 
                    value={taskDesc} 
                    onChange={e => setTaskDesc(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white" 
                    placeholder="Provide description details" 
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white font-bold rounded-lg text-[10px] uppercase tracking-wider">Save Task</button>
              </div>
            </form>
          )}

          <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
            {tasks.length === 0 ? (
              <div className="p-6 text-center text-xs text-zinc-500">No scheduled tasks pending.</div>
            ) : (
              tasks.map(task => (
                <div key={task.id} className={`p-4 rounded-xl border flex items-center justify-between transition ${task.status === 'Completed' ? 'bg-zinc-950/40 border-zinc-900 text-zinc-500' : 'bg-zinc-950 border-zinc-800'}`}>
                  <div className="flex items-center gap-3">
                    <button onClick={() => handleToggleTask(task.id, task.status)} className={`focus:outline-none ${task.status === 'Completed' ? 'text-emerald-500' : 'text-zinc-500 hover:text-white'}`}>
                      {task.status === 'Completed' ? <CheckCircle2 size={18} /> : <Clock size={18} />}
                    </button>
                    <div>
                      <h5 className={`text-xs font-bold ${task.status === 'Completed' ? 'line-through' : 'text-white'}`}>{task.title}</h5>
                      <p className="text-[10px] text-zinc-500 mt-0.5">{task.description}</p>
                      <div className="flex gap-2 mt-1.5 text-[9px] font-bold uppercase tracking-wider">
                        {task.lead_name && <span className="px-2 py-0.5 bg-indigo-950 border border-indigo-900 text-indigo-400 rounded-full">{task.lead_name}</span>}
                        <span className="px-2 py-0.5 bg-zinc-900 border border-zinc-800 text-zinc-400 rounded-full">Due: {new Date(task.due_date).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  <button onClick={() => handleDeleteTask(task.id)} className="text-zinc-500 hover:text-red-400 p-1">
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* CRM Calendar widget */}
        <div className="p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-white tracking-wide uppercase">Action Calendar</h4>
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Active agenda checklist items</span>
          </div>

          <div className="p-4 bg-zinc-950 rounded-xl border border-zinc-850 space-y-3">
            <div className="flex justify-between items-center text-[10px] font-bold text-zinc-500 uppercase tracking-wider border-b border-zinc-850 pb-2">
              <span>Timeline Agenda</span>
              <Calendar size={12} className="text-indigo-400" />
            </div>
            
            <div className="space-y-3 text-xs max-h-64 overflow-y-auto">
              {tasks.filter(t => t.status === 'Pending').map(t => {
                const isOverdue = new Date(t.due_date) < new Date()
                return (
                  <div key={t.id} className="flex gap-3 items-start p-2 rounded-lg bg-zinc-900/30 border border-zinc-800/40">
                    <span className={`w-2 h-2 mt-1.5 rounded-full ${isOverdue ? 'bg-red-500 animate-pulse' : 'bg-indigo-400'}`}></span>
                    <div>
                      <p className="font-bold text-white">{t.title}</p>
                      <p className="text-[9px] text-zinc-400 mt-0.5">{new Date(t.due_date).toLocaleDateString()} @ {new Date(t.due_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                    </div>
                  </div>
                )
              })}
              {tasks.filter(t => t.status === 'Pending').length === 0 && (
                <p className="text-[10px] text-zinc-500 text-center py-4">No pending scheduling items.</p>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
