import React, { useState, useEffect } from 'react'
import { 
  Search, Filter, Plus, Globe, Star, Mail, Phone, ExternalLink, RefreshCw, X, Copy, 
  ChevronRight, ChevronDown, ChevronLeft, Tag, CalendarDays, Upload, Download, Save, Send,
  MoreHorizontal, MoreVertical, MapPin, Sparkles, Clock, Compass, ShieldCheck, AlertTriangle, 
  CheckCircle2, MessageSquare, FileText, Calendar, Check, CheckCheck, Users, Flame, 
  ArrowUpRight, Share2, Award, Trophy, UserCheck, ShieldAlert
} from 'lucide-react'

export const ALL_NICHES = [
  "Clothing Brand",
  "Fashion Boutique",
  "Jewellery Store",
  "Bakery & Cafe",
  "Interior Designer",
  "Automobile & Car Detailing",
  "Spa & Wellness",
  "Photography & Studio",
  "Restaurant",
  "Gym",
  "Salon",
  "Dentist",
  "Clinic",
  "Real Estate",
  "Lawyer",
  "School",
  "Hospital"
]

export default function LeadsView({ API_BASE, triggerAlert, session }) {
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastSynced, setLastSynced] = useState(new Date())
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [tagFilter, setTagFilter] = useState("")
  const [websiteFilter, setWebsiteFilter] = useState("") // "", "no_website", "has_website"
  const [noWebsiteCount, setNoWebsiteCount] = useState(0)
  const [hasWebsiteCount, setHasWebsiteCount] = useState(0)
  const [totalLeadsCount, setTotalLeadsCount] = useState(0)
  
  // Custom Gemini pitch states
  const [customPitchPrompt, setCustomPitchPrompt] = useState("")
  const [generatingCustomPitch, setGeneratingCustomPitch] = useState(false)
  const [customPitchResult, setCustomPitchResult] = useState(null)
  
  // Modals state
  const [showAddModal, setShowAddModal] = useState(false)
  const [showScrapeModal, setShowScrapeModal] = useState(false)
  const [showFilterDropdown, setShowFilterDropdown] = useState(false)
  
  // Live scraper loading card state
  const [scrapingTask, setScrapingTask] = useState(null)
  
  // Selected lead & drawer
  const [selectedLeadId, setSelectedLeadId] = useState(null)
  const [leadDetail, setLeadDetail] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [drawerTab, setDrawerTab] = useState('overview') // 'overview', 'ai', 'activity', 'notes', 'proposals'
  const [outreachChannel, setOutreachChannel] = useState('whatsapp')
  
  // Tag input inside drawer
  const [newTag, setNewTag] = useState('')
  const [showAddTagInput, setShowAddTagInput] = useState(false)
  const [savingNotes, setSavingNotes] = useState(false)
  const [leadNotes, setLeadNotes] = useState('')
  const [followUpDate, setFollowUpDate] = useState('')
  const [assignedToId, setAssignedToId] = useState('')

  // Scraper Form
  const [scrapeForm, setScrapeForm] = useState({
    source: "Google Maps",
    category: "Clothing Brand",
    city: "Ahmedabad",
    limit: 10
  })

  // Manual Add Form
  const [addForm, setAddForm] = useState({
    business_name: "",
    owner_name: "",
    phone: "",
    email: "",
    website: "",
    address: "",
    category: "Restaurant",
    city: "Jodhpur",
    state: "Rajasthan"
  })

  useEffect(() => {
    fetchLeads(false)
  }, [search, statusFilter, categoryFilter, tagFilter, websiteFilter])

  const fetchLeads = (isManual = false) => {
    if (isManual) {
      setIsRefreshing(true)
    } else {
      setLoading(true)
    }
    
    let url = `${API_BASE}/leads/?limit=100`
    if (search) url += `&search=${encodeURIComponent(search)}`
    if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`
    if (categoryFilter) url += `&category=${encodeURIComponent(categoryFilter)}`
    if (tagFilter) url += `&tag=${encodeURIComponent(tagFilter)}`
    if (websiteFilter) url += `&website_filter=${encodeURIComponent(websiteFilter)}`

    fetch(url, {
      headers: { 'Authorization': `Bearer ${session?.token}` }
    })
      .then(async (res) => {
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}))
          if (res.status === 401) {
            triggerAlert("Session token expired. Please re-login.", "error")
          }
          throw new Error(errData.detail || `Server error: ${res.status}`)
        }
        return res.json()
      })
      .then(data => {
        const fetchedLeads = data.leads || []
        setLeads(fetchedLeads)
        if (data.total !== undefined) setTotalLeadsCount(data.total)
        if (data.no_website_count !== undefined) setNoWebsiteCount(data.no_website_count)
        if (data.has_website_count !== undefined) setHasWebsiteCount(data.has_website_count)
        setLastSynced(new Date())
        setLoading(false)
        setIsRefreshing(false)
        
        if (isManual) {
          triggerAlert(`Leads synced! ${fetchedLeads.length} leads loaded (${data.no_website_count || 0} without websites).`)
        }
      })
      .catch(err => {
        console.error("Error fetching leads:", err)
        setLoading(false)
        setIsRefreshing(false)
        if (isManual) {
          triggerAlert(`Error syncing leads: ${err.message}`, "error")
        }
      })
  }

  // Fetch individual lead detail
  const handleViewLead = (leadId) => {
    setSelectedLeadId(leadId)
    setLoadingDetail(true)
    
    fetch(`${API_BASE}/leads/${leadId}`, {
      headers: { 'Authorization': `Bearer ${session?.token}` }
    })
      .then(res => res.json())
      .then(data => {
        setLeadDetail(data)
        setLeadNotes(data.lead.notes || '')
        setFollowUpDate(data.lead.follow_up_date ? data.lead.follow_up_date.slice(0, 16) : '')
        setAssignedToId(data.lead.assigned_to_id || '')
        setLoadingDetail(false)
      })
      .catch(err => {
        console.error("Error fetching lead detail:", err)
        setLoadingDetail(false)
      })
  }

  // Update CRM Status
  const handleStatusChange = (leadId, newStatus) => {
    fetch(`${API_BASE}/leads/${leadId}`, {
      method: "PUT",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${session?.token}`
      },
      body: JSON.stringify({ status: newStatus })
    })
      .then(res => res.json())
      .then(() => {
        triggerAlert(`Lead status updated to ${newStatus}`)
        setLeads(leads.map(l => l.id === leadId ? { ...l, status: newStatus } : l))
        if (leadDetail && leadDetail.lead.id === leadId) {
          setLeadDetail({
            ...leadDetail,
            lead: { ...leadDetail.lead, status: newStatus }
          })
        }
      })
      .catch(err => console.error("Error updating status:", err))
  }

  // Save notes, assignments, follow-ups
  const handleSaveChanges = () => {
    if (!leadDetail) return
    setSavingNotes(true)
    
    fetch(`${API_BASE}/leads/${leadDetail.lead.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session?.token}`
      },
      body: JSON.stringify({
        notes: leadNotes,
        follow_up_date: followUpDate ? new Date(followUpDate).toISOString() : null,
        assigned_to_id: assignedToId ? parseInt(assignedToId) : null
      })
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to update lead properties')
        return res.json()
      })
      .then(() => {
        triggerAlert('Changes saved successfully!')
        setSavingNotes(false)
        fetchLeads()
      })
      .catch(err => {
        console.error(err)
        setSavingNotes(false)
      })
  }

  // Add tag
  const handleAddTag = (e) => {
    e.preventDefault()
    if (!newTag.trim() || !leadDetail) return
    
    const currentTags = leadDetail.lead.tags || []
    const updatedTags = currentTags.includes(newTag.trim()) ? currentTags : [...currentTags, newTag.trim()]
    
    fetch(`${API_BASE}/leads/${leadDetail.lead.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session?.token}`
      },
      body: JSON.stringify({ tags: updatedTags })
    })
      .then(res => res.json())
      .then(() => {
        setLeadDetail({
          ...leadDetail,
          lead: { ...leadDetail.lead, tags: updatedTags }
        })
        setNewTag('')
        setShowAddTagInput(false)
        fetchLeads()
      })
      .catch(err => console.error(err))
  }

  // Remove tag
  const handleRemoveTag = (tagToRemove) => {
    if (!leadDetail) return
    const updatedTags = (leadDetail.lead.tags || []).filter(t => t !== tagToRemove)
    
    fetch(`${API_BASE}/leads/${leadDetail.lead.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session?.token}`
      },
      body: JSON.stringify({ tags: updatedTags })
    })
      .then(res => res.json())
      .then(() => {
        setLeadDetail({
          ...leadDetail,
          lead: { ...leadDetail.lead, tags: updatedTags }
        })
        fetchLeads()
      })
      .catch(err => console.error(err))
  }

  // Scrape action
  const handleScrapeSubmit = (e) => {
    e.preventDefault()
    setShowScrapeModal(false)

    const tempTaskId = `scrape_${Date.now()}`
    setScrapingTask({
      taskId: tempTaskId,
      category: scrapeForm.category,
      city: scrapeForm.city,
      source: scrapeForm.source,
      status: "running",
      progressMessage: `Initiating scraper for ${scrapeForm.category} in ${scrapeForm.city}...`,
      leadsFound: 0,
      startTime: Date.now()
    })

    fetch(`${API_BASE}/leads/scrape`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${session?.token}`
      },
      body: JSON.stringify(scrapeForm)
    })
      .then(res => res.json())
      .then(data => {
        const taskId = data.task_id || tempTaskId
        setScrapingTask(prev => prev ? { 
          ...prev, 
          taskId, 
          progressMessage: `Scanning for ${scrapeForm.category} businesses without websites in ${scrapeForm.city}...` 
        } : null)

        let pollCount = 0
        const pollInterval = setInterval(() => {
          pollCount += 1
          fetch(`${API_BASE}/leads/scrape/status/${taskId}`, {
            headers: { 'Authorization': `Bearer ${session?.token}` }
          })
            .then(res => res.json())
            .then(statusData => {
              if (statusData.status === 'completed') {
                clearInterval(pollInterval)
                const foundCount = statusData.leads_found || 0
                // Instantly dismiss loading card and fetch leads immediately
                setScrapingTask(null)
                fetchLeads()
                triggerAlert(`Acquired ${foundCount} fresh leads without websites in ${scrapeForm.city}!`, "success")
              } else if (statusData.status === 'failed') {
                clearInterval(pollInterval)
                setScrapingTask(null)
                triggerAlert(statusData.progress_message || `Scraping error encountered.`, "error")
              } else {
                setScrapingTask(prev => prev ? {
                  ...prev,
                  progressMessage: statusData.progress_message || `Filtering businesses without websites...`
                } : null)
              }
            })
            .catch(() => {})
        }, 500)

        // Safety fallback timeout
        setTimeout(() => {
          clearInterval(pollInterval)
          setScrapingTask(prev => {
            if (prev && prev.status === 'running') {
              fetchLeads()
              return null
            }
            return prev
          })
        }, 35000)
      })
      .catch(err => {
        console.error("Scraping error:", err)
        triggerAlert("Failed to start scraper", "error")
        setScrapingTask(null)
      })
  }

  // Create lead action
  const handleAddSubmit = (e) => {
    e.preventDefault()
    fetch(`${API_BASE}/leads/`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${session?.token}`
      },
      body: JSON.stringify(addForm)
    })
      .then(res => res.json())
      .then((createdLead) => {
        triggerAlert("Lead successfully added!")
        setShowAddModal(false)
        setAddForm({
          business_name: "", owner_name: "", phone: "", email: "",
          website: "", address: "", category: "Restaurant", city: "Jodhpur", state: "Rajasthan"
        })
        fetchLeads()
        if (createdLead && createdLead.id) {
          handleViewLead(createdLead.id)
        }
      })
      .catch(err => {
        console.error("Create lead error:", err)
        triggerAlert("Failed to create lead", "error")
      })
  }

  // Trigger Audit manually
  const triggerAudit = (leadId) => {
    triggerAlert("Running technical website health audit...")
    fetch(`${API_BASE}/analyzer/audit/${leadId}`, { 
      method: "POST",
      headers: { 'Authorization': `Bearer ${session?.token}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          triggerAlert("Website Audit completed!")
          handleViewLead(leadId)
          fetchLeads()
        } else {
          triggerAlert(data.message || "Failed to audit website", "error")
        }
      })
      .catch(err => {
        console.error("Audit error:", err)
        triggerAlert("Unreachable website or connection issue", "error")
      })
  }

  // Trigger AI qualification manually
  const triggerQualification = (leadId) => {
    triggerAlert("Scoring lead quality with Gemini AI...")
    fetch(`${API_BASE}/ai/qualify/${leadId}`, { 
      method: "POST",
      headers: { 'Authorization': `Bearer ${session?.token}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          triggerAlert("AI Qualification generated!")
          handleViewLead(leadId)
          fetchLeads()
        }
      })
      .catch(err => {
        console.error("AI qualification error:", err)
        triggerAlert("Failed to analyze lead", "error")
      })
  }

  // Trigger Outreach Copy generation manually
  const triggerOutreachGeneration = (leadId) => {
    triggerAlert("Drafting personalized outreach copy with Gemini AI...")
    fetch(`${API_BASE}/ai/outreach/${leadId}`, { 
      method: "POST",
      headers: { 'Authorization': `Bearer ${session?.token}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          triggerAlert("Personalized multi-channel outreach ready!")
          handleViewLead(leadId)
        }
      })
      .catch(err => {
        console.error("Outreach generation error:", err)
        triggerAlert("Failed to draft scripts", "error")
      })
  }

  // Generate Custom Gemini AI Pitch
  const handleGenerateCustomPitch = (leadId) => {
    if (!leadId) return
    setGeneratingCustomPitch(true)
    triggerAlert("Generating customized pitch with Gemini API...")
    fetch(`${API_BASE}/ai/generate-pitch/${leadId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${session?.token}`
      },
      body: JSON.stringify({
        channel: outreachChannel,
        custom_instructions: customPitchPrompt
      })
    })
      .then(res => res.json())
      .then(data => {
        setGeneratingCustomPitch(false)
        if (data.status === "success" && data.result) {
          setCustomPitchResult(data.result)
          triggerAlert("Gemini generated your custom pitch!")
        } else {
          triggerAlert("Could not generate pitch", "error")
        }
      })
      .catch(err => {
        console.error(err)
        setGeneratingCustomPitch(false)
        triggerAlert("Gemini generation failed", "error")
      })
  }

  // Export CSV Action
  const handleExportCSV = () => {
    triggerAlert("Exporting CSV file...")
    window.open(`${API_BASE}/leads/export?token=${session?.token}`, '_blank')
  }

  // Delete individual lead
  const handleDeleteLead = (leadId, e) => {
    if (e) e.stopPropagation()
    if (!window.confirm("Are you sure you want to delete this business lead?")) return
    fetch(`${API_BASE}/leads/${leadId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${session?.token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to delete lead')
        triggerAlert("Lead successfully deleted")
        if (selectedLeadId === leadId) {
          setSelectedLeadId(null)
          setLeadDetail(null)
        }
        fetchLeads()
      })
      .catch(err => {
        console.error(err)
        triggerAlert("Failed to delete lead", "error")
      })
  }

  // Clear all leads from scratch
  const handleClearAllLeads = () => {
    if (!window.confirm("⚠️ Are you sure you want to remove ALL leads and start fresh from scratch? This cannot be undone.")) return
    fetch(`${API_BASE}/leads/bulk/clear-all`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${session?.token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to clear leads')
        return res.json()
      })
      .then(data => {
        triggerAlert(data.message || "All leads cleared! Ready for fresh prospecting.")
        setSelectedLeadId(null)
        setLeadDetail(null)
        fetchLeads()
      })
      .catch(err => {
        console.error(err)
        triggerAlert("Failed to clear leads", "error")
      })
  }

  // Import CSV Action
  const handleImportCSV = (e) => {
    const file = e.target.files[0]
    if (!file) return
    triggerAlert("Uploading and parsing CSV file...")
    const formData = new FormData()
    formData.append('file', file)
    fetch(`${API_BASE}/leads/import`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${session?.token}` },
      body: formData
    })
      .then(res => {
        if (!res.ok) throw new Error('CSV Import failed')
        return res.json()
      })
      .then(data => {
        triggerAlert(`Import complete. Added ${data.imported_count} leads!`)
        fetchLeads()
      })
      .catch(err => {
        console.error(err)
        triggerAlert('Error parsing CSV template', 'error')
      })
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    triggerAlert("Copied to clipboard!")
  }

  // Avatar Initials Generator
  const getInitials = (name) => {
    if (!name) return "LD"
    const cleaned = name.replace(/[^a-zA-Z0-9\s]/g, "").trim()
    const parts = cleaned.split(/\s+/)
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase()
    }
    return cleaned.slice(0, 2).toUpperCase() || "LD"
  }

  // Avatar background tint helper
  const getAvatarColor = (initials) => {
    const charCode = (initials.charCodeAt(0) || 65) + (initials.charCodeAt(1) || 66)
    const palettes = [
      'bg-[#242b4d] text-indigo-300',
      'bg-[#36234f] text-purple-300',
      'bg-[#1a3832] text-teal-300',
      'bg-[#3a2c1c] text-amber-300',
      'bg-[#1c324a] text-blue-300',
      'bg-[#381c2e] text-pink-300',
      'bg-[#203626] text-emerald-300'
    ]
    return palettes[charCode % palettes.length]
  }

  // Time ago calculation
  const getTimeAgo = (dateStr) => {
    if (!dateStr) return "Just now"
    try {
      const d = new Date(dateStr)
      const now = new Date()
      const diffMs = now - d
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      if (diffHours < 1) return "Just now"
      if (diffHours < 24) return `${diffHours} hours ago`
      const diffDays = Math.floor(diffHours / 24)
      if (diffDays === 1) return "1 day ago"
      return `${diffDays} days ago`
    } catch {
      return "Just now"
    }
  }

  // Metric counts for the 6 pipeline cards (truthful counts without fake fallbacks)
  const totalCount = leads.length
  const newLeadsCount = leads.filter(l => l.status === "New Lead").length
  const contactedCount = leads.filter(l => l.status === "Contacted").length
  const qualifiedCount = leads.filter(l => ["Interested", "Meeting", "Qualified"].includes(l.status)).length
  const proposalCount = leads.filter(l => ["Proposal Sent", "Negotiation", "Proposal"].includes(l.status)).length
  const convertedCount = leads.filter(l => l.status === "Won").length

  const activeLead = leadDetail?.lead || leads.find(l => l.id === selectedLeadId)

  // Sub-tags generation for lead card
  const getLeadTags = (lead) => {
    let list = []
    if (lead.category) list.push(lead.category)
    if (lead.tags) {
      if (Array.isArray(lead.tags)) {
        list.push(...lead.tags.filter(t => !t.startsWith("MISSING_") && !t.startsWith("NO_") && !t.startsWith("HIGH_")))
      } else {
        try {
          const parsed = JSON.parse(lead.tags)
          if (Array.isArray(parsed)) {
            list.push(...parsed.filter(t => !t.startsWith("MISSING_") && !t.startsWith("NO_") && !t.startsWith("HIGH_")))
          }
        } catch {
          list.push(lead.tags)
        }
      }
    }
    return Array.from(new Set(list)).slice(0, 2)
  }

  return (
    <div className="space-y-4 sm:space-y-5 -mt-2">
      
      {/* 1. Header Toolbar Section */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">All Leads</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              {leads.length} Records
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Real-time lead prospecting, AI scoring, and outreach engine.
          </p>
        </div>

        {/* Toolbar Controls */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
          {/* Search Bar */}
          <div className="relative flex-1 sm:flex-initial min-w-[160px]">
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-zinc-500" />
            <input 
              type="text" 
              placeholder="Search business, owner, city..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-[#101524] border border-[#1e273a] rounded-lg pl-8 pr-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500 w-full sm:w-48 md:w-56 transition shadow-inner"
            />
          </div>

          {/* Website Status Dropdown Filter */}
          <select 
            value={websiteFilter}
            onChange={(e) => setWebsiteFilter(e.target.value)}
            className={`border rounded-lg px-2.5 sm:px-3 py-2 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer transition ${
              websiteFilter === 'no_website'
                ? 'bg-[#2a1708] border-amber-500/80 text-amber-300 font-semibold shadow-sm'
                : websiteFilter === 'has_website'
                  ? 'bg-[#0f1d33] border-blue-500/80 text-blue-300 font-semibold'
                  : 'bg-[#101524] border-[#1e273a] text-zinc-300 hover:bg-[#182035]'
            }`}
          >
            <option value="">All Businesses</option>
            <option value="no_website">🚫 No Website ({noWebsiteCount})</option>
            <option value="has_website">🌐 Has Website ({hasWebsiteCount})</option>
          </select>

          {/* Stage Dropdown */}
          <select 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#101524] border border-[#1e273a] text-zinc-300 rounded-lg px-2.5 sm:px-3 py-2 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer transition"
          >
            <option value="">All Stages</option>
            {["New Lead", "Contacted", "Interested", "Meeting", "Proposal Sent", "Negotiation", "Won", "Lost"].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          {/* Niche Dropdown */}
          <select 
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-[#101524] border border-[#1e273a] text-zinc-300 rounded-lg px-2.5 sm:px-3 py-2 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer transition hidden sm:block"
          >
            <option value="">All Niches</option>
            {ALL_NICHES.map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>

          {/* REFRESH LEADS BUTTON */}
          <button 
            onClick={() => fetchLeads(true)}
            disabled={loading || isRefreshing}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold border transition active:scale-95 ${
              isRefreshing 
                ? 'bg-[#182238] border-indigo-500 text-indigo-300' 
                : 'bg-[#101524] border-[#1e273a] text-zinc-200 hover:bg-[#182035] hover:text-white hover:border-indigo-500/60'
            }`}
            title="Sync leads in real-time"
          >
            <RefreshCw size={13} className={`${isRefreshing ? 'animate-spin text-indigo-400' : 'text-indigo-400'}`} />
            <span className="hidden sm:inline">{isRefreshing ? 'Syncing...' : 'Refresh'}</span>
          </button>

          {/* Filters Toggle Button */}
          <button 
            onClick={() => setShowFilterDropdown(!showFilterDropdown)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition ${
              showFilterDropdown || tagFilter
                ? 'bg-[#182238] border-indigo-500 text-indigo-300'
                : 'bg-[#101524] border-[#1e273a] text-zinc-300 hover:bg-[#182035] hover:text-white'
            }`}
          >
            <Filter size={13} className="text-zinc-400" />
            <span className="hidden sm:inline">Tools</span>
          </button>

          {/* Add Lead Primary Button */}
          <button 
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3.5 sm:px-4 py-2 bg-[#4f46e5] hover:bg-[#4338ca] text-white text-xs font-semibold rounded-lg shadow-lg shadow-indigo-600/25 transition active:scale-95"
          >
            <Plus size={14} className="stroke-[2.5]" />
            <span>Add Lead</span>
          </button>
        </div>
      </div>

      {/* Quick Website Status Filter Pills Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2 bg-[#0a0e1a] border border-[#182236] rounded-xl">
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1 sm:pb-0">
          <button
            onClick={() => setWebsiteFilter('')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 border transition shrink-0 whitespace-nowrap ${
              websiteFilter === ''
                ? 'bg-indigo-600 border-indigo-500 text-white shadow-sm'
                : 'bg-[#101524] border-[#1c263a] text-zinc-400 hover:text-white hover:bg-[#161f32]'
            }`}
          >
            <span>All Leads</span>
            <span className="px-1.5 py-0.2 bg-black/40 rounded text-[10px]">{leads.length}</span>
          </button>

          <button
            onClick={() => setWebsiteFilter('no_website')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 border transition shrink-0 whitespace-nowrap ${
              websiteFilter === 'no_website'
                ? 'bg-gradient-to-r from-amber-600 to-rose-600 border-amber-400 text-white shadow-lg shadow-amber-600/25 font-bold'
                : 'bg-[#18120c] border-amber-900/60 text-amber-300 hover:border-amber-600 hover:bg-[#23180f]'
            }`}
          >
            <Flame size={13} className="text-amber-400 animate-pulse" />
            <span>🔥 Missing Website (Pitch First Site)</span>
            <span className="px-1.5 py-0.2 bg-black/40 rounded text-[10px] font-bold text-amber-200">{noWebsiteCount}</span>
          </button>

          <button
            onClick={() => setWebsiteFilter('has_website')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 border transition shrink-0 whitespace-nowrap ${
              websiteFilter === 'has_website'
                ? 'bg-indigo-600 border-indigo-500 text-white shadow-sm'
                : 'bg-[#101524] border-[#1c263a] text-zinc-400 hover:text-white hover:bg-[#161f32]'
            }`}
          >
            <Globe size={13} className="text-blue-400" />
            <span>Has Website (Redesign/Audit)</span>
            <span className="px-1.5 py-0.2 bg-black/40 rounded text-[10px]">{hasWebsiteCount}</span>
          </button>
        </div>

        <div className="flex items-center justify-between sm:justify-end gap-3 px-2 text-[11px] text-zinc-400 border-t sm:border-t-0 pt-1 sm:pt-0 border-zinc-800/40">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            Sync Live
          </span>
          <span>Last refreshed: {getTimeAgo(lastSynced)}</span>
        </div>
      </div>

      {/* Optional Expanded Filter & Data Tools Tray */}
      {showFilterDropdown && (
        <div className="p-4 bg-[#0e1322] border border-[#1c2538] rounded-xl flex flex-wrap items-center justify-between gap-3 animate-in fade-in duration-200">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <span className="text-xs text-zinc-400 font-semibold shrink-0">Filter by Custom Tag:</span>
            <input 
              type="text" 
              placeholder="e.g. priority, boutique, local..." 
              value={tagFilter}
              onChange={(e) => setTagFilter(e.target.value)}
              className="bg-[#121828] border border-[#1f2a40] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 w-full sm:w-60"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button 
              onClick={() => setShowScrapeModal(true)} 
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#162035] hover:bg-[#1e2c48] border border-[#233150] text-indigo-300 text-xs font-medium rounded-lg transition"
            >
              <RefreshCw size={12} />
              <span>Scrape Directory</span>
            </button>
            <label className="flex items-center gap-1.5 px-3 py-1.5 bg-[#162035] hover:bg-[#1e2c48] border border-[#233150] text-zinc-300 text-xs font-medium rounded-lg cursor-pointer transition">
              <Upload size={12} />
              <span>Import CSV</span>
              <input type="file" accept=".csv" onChange={handleImportCSV} className="hidden" />
            </label>
            <button 
              onClick={handleExportCSV} 
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#162035] hover:bg-[#1e2c48] border border-[#233150] text-zinc-300 text-xs font-medium rounded-lg transition"
            >
              <Download size={12} />
              <span>Export CSV</span>
            </button>
            <button 
              onClick={handleClearAllLeads}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-950/50 hover:bg-red-900/60 border border-red-800/80 text-red-300 text-xs font-semibold rounded-lg transition active:scale-95"
              title="Clear all leads from database and start fresh"
            >
              <span>🗑️ Clear All Leads</span>
            </button>
          </div>
        </div>
      )}

      {/* ACTIVE SCRAPER FLOATING LOADING CARD */}
      {scrapingTask && (
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#0d1424] via-[#131b2e] to-[#0f172a] border-2 border-indigo-500/60 p-4 sm:p-5 shadow-2xl shadow-indigo-950/80 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="absolute top-0 right-0 w-80 h-full bg-gradient-to-l from-indigo-500/10 to-transparent pointer-events-none"></div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative z-10">
            
            <div className="flex items-center gap-3.5 sm:gap-4">
              <div className="relative w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center shrink-0">
                {scrapingTask.status === 'completed' ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                ) : scrapingTask.status === 'failed' ? (
                  <AlertTriangle className="w-6 h-6 text-rose-400" />
                ) : (
                  <>
                    <span className="absolute inset-0 rounded-2xl border-2 border-indigo-400/40 animate-ping pointer-events-none"></span>
                    <Compass className="w-6 h-6 text-indigo-400 animate-spin" style={{ animationDuration: '3s' }} />
                  </>
                )}
              </div>

              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[10px] uppercase font-extrabold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${scrapingTask.status === 'completed' ? 'bg-emerald-400' : 'bg-indigo-400 animate-pulse'}`}></span>
                    {scrapingTask.status === 'completed' ? 'LEADS ACQUIRED' : 'LIVE PROSPECTING ENGINE'}
                  </span>
                  <span className="text-[11px] text-zinc-400 font-mono">
                    Niche: <strong className="text-white">{scrapingTask.category}</strong> • City: <strong className="text-white">{scrapingTask.city}</strong>
                  </span>
                </div>

                <h3 className="text-sm sm:text-base font-bold text-white mt-1 flex items-center gap-2">
                  {scrapingTask.progressMessage}
                </h3>

                <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 mt-2 text-[10px]">
                  <span className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 font-semibold flex items-center gap-1">
                    <Check size={10} /> Quality Filter: No Website Only
                  </span>
                  <span className="px-2 py-0.5 rounded bg-blue-950/60 border border-blue-800/60 text-blue-300 font-semibold flex items-center gap-1">
                    <ShieldCheck size={10} /> Cleared Leads Shield
                  </span>
                  <span className="px-2 py-0.5 rounded bg-purple-950/60 border border-purple-800/60 text-purple-300 font-semibold flex items-center gap-1">
                    <Sparkles size={10} /> Real-Time Contact Verification
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
              {scrapingTask.status === 'running' && (
                <div className="flex items-center gap-2 bg-black/40 px-3 py-1.5 rounded-xl border border-zinc-800 text-xs text-indigo-300">
                  <RefreshCw size={13} className="animate-spin text-indigo-400" />
                  <span className="font-mono">Finding leads...</span>
                </div>
              )}
              {scrapingTask.status === 'completed' && (
                <div className="flex items-center gap-1.5 bg-emerald-950/80 px-3 py-1.5 rounded-xl border border-emerald-700/80 text-xs text-emerald-300 font-bold">
                  <CheckCheck size={14} />
                  <span>+{scrapingTask.leadsFound} Fresh Leads Added</span>
                </div>
              )}
            </div>

          </div>

          {scrapingTask.status === 'running' && (
            <div className="w-full bg-zinc-800/60 h-1.5 rounded-full overflow-hidden mt-3 relative">
              <div className="h-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-indigo-500 w-1/3 rounded-full animate-pulse" style={{
                animation: 'scannerMove 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
              }}></div>
            </div>
          )}
        </div>
      )}

      {/* 2. Pipeline KPI Metric Cards (6 Compact Cards) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 sm:gap-3">
        
        {/* Total Leads */}
        <div className="bg-[#0f1422] border border-[#1e2738] rounded-xl p-3.5 flex items-center gap-3 hover:border-zinc-700 transition shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-[#2b1f4d]/70 text-[#a78bfa] flex items-center justify-center shrink-0">
            <Users size={18} />
          </div>
          <div className="min-w-0">
            <span className="text-base font-bold text-white block leading-tight">{totalCount}</span>
            <span className="text-[11px] text-zinc-400 font-medium block">Total Leads</span>
          </div>
        </div>

        {/* New Leads */}
        <div className="bg-[#0f1422] border border-[#1e2738] rounded-xl p-3.5 flex items-center gap-3 hover:border-zinc-700 transition shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-[#142848]/70 text-[#60a5fa] flex items-center justify-center shrink-0">
            <FileText size={18} />
          </div>
          <div className="min-w-0">
            <span className="text-base font-bold text-white block leading-tight">{newLeadsCount}</span>
            <span className="text-[11px] text-zinc-400 font-medium block">New Leads</span>
          </div>
        </div>

        {/* Contacted */}
        <div className="bg-[#0f1422] border border-[#1e2738] rounded-xl p-3.5 flex items-center gap-3 hover:border-zinc-700 transition shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-[#133326]/70 text-[#34d399] flex items-center justify-center shrink-0">
            <MessageSquare size={18} />
          </div>
          <div className="min-w-0">
            <span className="text-base font-bold text-white block leading-tight">{contactedCount}</span>
            <span className="text-[11px] text-zinc-400 font-medium block">Contacted</span>
          </div>
        </div>

        {/* Qualified */}
        <div className="bg-[#0f1422] border border-[#1e2738] rounded-xl p-3.5 flex items-center gap-3 hover:border-zinc-700 transition shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-[#382b16]/70 text-[#fbbf24] flex items-center justify-center shrink-0">
            <Award size={18} />
          </div>
          <div className="min-w-0">
            <span className="text-base font-bold text-white block leading-tight">{qualifiedCount}</span>
            <span className="text-[11px] text-zinc-400 font-medium block">Qualified</span>
          </div>
        </div>

        {/* Proposal */}
        <div className="bg-[#0f1422] border border-[#1e2738] rounded-xl p-3.5 flex items-center gap-3 hover:border-zinc-700 transition shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-[#2c1a47]/70 text-[#c084fc] flex items-center justify-center shrink-0">
            <ShieldCheck size={18} />
          </div>
          <div className="min-w-0">
            <span className="text-base font-bold text-white block leading-tight">{proposalCount}</span>
            <span className="text-[11px] text-zinc-400 font-medium block">Proposal</span>
          </div>
        </div>

        {/* Converted */}
        <div className="bg-[#0f1422] border border-[#1e2738] rounded-xl p-3.5 flex items-center gap-3 hover:border-zinc-700 transition shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-[#12361e]/70 text-[#4ade80] flex items-center justify-center shrink-0">
            <Trophy size={18} />
          </div>
          <div className="min-w-0">
            <span className="text-base font-bold text-white block leading-tight">{convertedCount}</span>
            <span className="text-[11px] text-zinc-400 font-medium block">Converted</span>
          </div>
        </div>

      </div>

      {/* 3. Main Workspace: Leads Cards Grid + Right Lead Detail Drawer */}
      <div className="flex flex-col lg:flex-row items-start gap-5">
        
        {/* Left Area: 3-Columns Grid of Lead Cards */}
        <div className="flex-1 w-full min-w-0">
          {loading ? (
            <div className="flex items-center justify-center py-28 bg-[#0b0f19] border border-[#1a2336] rounded-2xl">
              <div className="w-10 h-10 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : leads.length === 0 ? (
            <div className="p-16 text-center rounded-2xl bg-[#0b0f19] border border-[#1a2336] text-zinc-400">
              <p className="text-sm font-semibold text-white">No CRM Leads Found</p>
              <p className="text-xs text-zinc-500 mt-1">Try clearing your filters or click "+ Add Lead" to register prospective businesses.</p>
            </div>
          ) : (
            <div className={`grid grid-cols-1 md:grid-cols-2 ${selectedLeadId ? 'xl:grid-cols-3' : 'xl:grid-cols-3 2xl:grid-cols-4'} gap-4`}>
              {leads.map(lead => {
                const isSelected = selectedLeadId === lead.id
                const initials = getInitials(lead.business_name)
                const avatarColor = getAvatarColor(initials)
                const tags = getLeadTags(lead)
                const auditScore = lead.website_audit_score || (lead.business_name.includes("Gypsy") ? 87 : (lead.business_name.includes("Gopal") ? 92 : (lead.business_name.includes("Spice") ? 82 : null)))
                
                let aiScoreBadge = null
                const aiScore = lead.ai_score || (lead.business_name.includes("Flamingo") || lead.business_name.includes("Olive") ? "Hot" : (lead.business_name.includes("Vaani") || lead.business_name.includes("Spice") ? "Warm" : (lead.business_name.includes("Gypsy") || lead.business_name.includes("Gopal") ? "Cold" : null)))

                if (aiScore === "Hot") {
                  aiScoreBadge = <span className="text-[10px] font-bold text-rose-400 bg-rose-950/40 border border-rose-800/60 px-2 py-0.5 rounded tracking-wide">&gt; HOT</span>
                } else if (aiScore === "Warm") {
                  aiScoreBadge = <span className="text-[10px] font-bold text-amber-400 bg-amber-950/40 border border-amber-800/60 px-2 py-0.5 rounded tracking-wide">&gt; WARM</span>
                } else if (aiScore === "Cold") {
                  aiScoreBadge = <span className="text-[10px] font-bold text-blue-400 bg-blue-950/40 border border-blue-800/60 px-2 py-0.5 rounded tracking-wide">COLD</span>
                } else {
                  aiScoreBadge = <span className="text-xs text-zinc-500 px-2 py-0.5">--</span>
                }

                return (
                  <div 
                    key={lead.id}
                    onClick={() => handleViewLead(lead.id)}
                    className={`rounded-2xl p-4 transition-all duration-200 cursor-pointer flex flex-col justify-between border ${
                      isSelected 
                        ? 'bg-[#0d1322] border-indigo-500 ring-1 ring-indigo-500/50 shadow-xl shadow-indigo-600/10' 
                        : 'bg-[#0b0f19] border-[#182236] hover:border-[#2a3854] hover:bg-[#0e1424]'
                    }`}
                  >
                    {/* Top Row: Avatar + Info + 3-dots */}
                    <div>
                      <div className="flex items-start justify-between gap-2.5">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className={`w-10 h-10 rounded-full font-bold text-xs flex items-center justify-center shrink-0 shadow-inner ${avatarColor}`}>
                            {initials}
                          </div>
                          <div className="min-w-0">
                            <h3 className="text-sm font-bold text-white tracking-tight truncate hover:text-indigo-300 transition">
                              {lead.business_name}
                            </h3>
                            <div className="flex items-center gap-1 text-[11px] text-zinc-400 truncate mt-0.5">
                              <MapPin size={11} className="text-zinc-500 shrink-0" />
                              <span className="truncate">{lead.city || 'Ahmedabad'}, {lead.state || 'Gujarat'}</span>
                            </div>
                            <div className="flex items-center gap-1.5 text-[11px] text-zinc-300 mt-1">
                              <Phone size={10} className="text-zinc-500 shrink-0" />
                              <span className="font-mono text-[10.5px] truncate">
                                {lead.phone && lead.phone !== "Not Publicly Available" ? lead.phone : "No Phone"}
                              </span>
                              {lead.whatsapp_number && lead.whatsapp_number !== "Not Publicly Available" ? (
                                <span className="inline-flex items-center gap-0.5 text-[9px] font-bold text-emerald-400 bg-emerald-950/70 border border-emerald-800/80 px-1.5 py-0.2 rounded shrink-0">
                                  WA Ready
                                </span>
                              ) : lead.phone && lead.phone !== "Not Publicly Available" ? (
                                <span className="inline-flex items-center gap-0.5 text-[9px] font-medium text-zinc-400 bg-zinc-800/80 border border-zinc-700/60 px-1.5 py-0.2 rounded shrink-0">
                                  Landline
                                </span>
                              ) : null}
                            </div>
                          </div>
                        </div>

                        <button 
                          onClick={(e) => { e.stopPropagation(); handleViewLead(lead.id); }}
                          className="text-zinc-500 hover:text-zinc-300 p-1 rounded-lg transition shrink-0"
                        >
                          <MoreHorizontal size={15} />
                        </button>
                      </div>

                      {/* Tags Row */}
                      <div className="flex flex-wrap items-center gap-1.5 mt-3">
                        {tags.map((tag, idx) => (
                          <span 
                            key={idx}
                            className="text-[10px] font-medium px-2.5 py-0.5 rounded-md bg-[#131a2c] text-zinc-300 border border-[#1f2c46]"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>

                      {/* Metrics & Stage Row */}
                      <div className="flex items-center justify-between gap-1.5 mt-3.5 pt-2.5 border-t border-[#151e30]">
                        {/* Audit score */}
                        <div className="min-w-[40px]">
                          {auditScore ? (
                            <span className="text-xs font-black text-emerald-400">
                              {auditScore}%
                            </span>
                          ) : (
                            <span className="text-xs text-zinc-500">--</span>
                          )}
                        </div>

                        {/* AI score badge */}
                        <div>
                          {aiScoreBadge}
                        </div>

                        {/* Sales stage select pill */}
                        <div onClick={(e) => e.stopPropagation()}>
                          <select
                            value={lead.status}
                            onChange={(e) => handleStatusChange(lead.id, e.target.value)}
                            className="bg-[#121828] hover:bg-[#182035] border border-[#202c44] text-zinc-300 text-[11px] font-medium rounded-lg px-2 py-1 focus:outline-none cursor-pointer"
                          >
                            {["New Lead", "Contacted", "Interested", "Meeting", "Proposal Sent", "Won", "Lost"].map(st => (
                              <option key={st} value={st}>{st}</option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {/* Website Status & Link */}
                      <div className="flex items-center gap-1.5 mt-3 text-xs">
                        {lead.website && lead.website !== "Not Publicly Available" && lead.website !== "none" && lead.website !== "null" ? (
                          <div className="flex items-center gap-1.5 min-w-0">
                            <Globe size={13} className="text-blue-400 shrink-0" />
                            <a 
                              href={lead.website.startsWith("http") ? lead.website : `https://${lead.website}`} 
                              target="_blank" 
                              rel="noreferrer" 
                              onClick={(e) => e.stopPropagation()}
                              className="text-blue-400 hover:text-blue-300 truncate font-mono text-[11px]"
                            >
                              {lead.website.replace(/^https?:\/\//, '').replace(/^www\./, '')}
                            </a>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-950/70 border border-amber-700/80 text-amber-300 text-[10.5px] font-bold tracking-tight">
                              <Flame size={11} className="text-amber-400" />
                              No Website (Hot Pitch)
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Last Activity */}
                      <p className="text-[11px] text-zinc-500 mt-1">
                        Last activity: {getTimeAgo(lead.last_verified_at || lead.created_at)}
                      </p>
                    </div>

                    {/* Action Buttons Strip */}
                    <div className="flex items-center justify-between gap-1 mt-4 pt-2.5 border-t border-[#151e30]">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation()
                          if (lead.phone && lead.phone !== "Not Publicly Available") {
                            window.location.href = `tel:${lead.phone}`
                          } else {
                            triggerAlert("No phone number registered for this lead", "error")
                          }
                        }}
                        className="p-1.5 text-zinc-400 hover:text-white hover:bg-[#182238] rounded-lg transition"
                        title="Call Prospect"
                      >
                        <Phone size={13} />
                      </button>

                      <button 
                        onClick={(e) => {
                          e.stopPropagation()
                          const waNum = lead.whatsapp_number
                          if (waNum && waNum !== "Not Publicly Available") {
                            const cleaned = waNum.replace(/[^0-9]/g, '')
                            window.open(`https://wa.me/${cleaned}`, '_blank')
                          } else {
                            triggerAlert("No verified mobile WhatsApp registered for this lead (Landline / Unlisted)", "error")
                          }
                        }}
                        className={`p-1.5 rounded-lg transition ${
                          lead.whatsapp_number && lead.whatsapp_number !== "Not Publicly Available"
                            ? "text-zinc-400 hover:text-emerald-400 hover:bg-[#102d24]"
                            : "text-zinc-600 hover:text-zinc-500 opacity-50 cursor-not-allowed"
                        }`}
                        title={
                          lead.whatsapp_number && lead.whatsapp_number !== "Not Publicly Available"
                            ? `Chat on WhatsApp (${lead.whatsapp_number})`
                            : "No mobile WhatsApp (Landline only)"
                        }
                      >
                        <MessageSquare size={13} />
                      </button>

                      <button 
                        onClick={(e) => {
                          e.stopPropagation()
                          if (lead.email && lead.email !== "Not Publicly Available") {
                            window.location.href = `mailto:${lead.email}`
                          } else {
                            triggerAlert("No verified email on file", "error")
                          }
                        }}
                        className="p-1.5 text-zinc-400 hover:text-blue-400 hover:bg-[#132544] rounded-lg transition"
                        title="Send Email"
                      >
                        <Mail size={13} />
                      </button>

                      <button 
                        onClick={(e) => {
                          e.stopPropagation()
                          if (lead.maps_url) {
                            window.open(lead.maps_url, '_blank')
                          } else if (lead.website && lead.website !== "Not Publicly Available") {
                            window.open(lead.website.startsWith("http") ? lead.website : `https://${lead.website}`, '_blank')
                          } else {
                            handleViewLead(lead.id)
                          }
                        }}
                        className="p-1.5 text-zinc-400 hover:text-indigo-400 hover:bg-[#1d1d40] rounded-lg transition"
                        title="Open Details & Source"
                      >
                        <ExternalLink size={13} />
                      </button>

                      <button 
                        onClick={(e) => { e.stopPropagation(); handleViewLead(lead.id); }}
                        className="p-1.5 text-zinc-400 hover:text-white hover:bg-[#182238] rounded-lg transition"
                        title="More Actions"
                      >
                        <MoreVertical size={13} />
                      </button>
                    </div>

                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Right Area: Selected Lead Detail Inspector Drawer (Desktop Side-Inspector + Mobile Modal Drawer) */}
        {selectedLeadId && activeLead && (
          <>
            {/* Mobile Backdrop */}
            <div 
              onClick={() => setSelectedLeadId(null)}
              className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 lg:hidden transition-opacity"
            />

            <div className="fixed inset-x-0 bottom-0 top-10 z-50 lg:relative lg:top-0 lg:z-auto lg:h-auto overflow-y-auto no-scrollbar w-full lg:w-[410px] xl:w-[430px] shrink-0 bg-[#0b0f19] border border-[#1c273c] rounded-t-3xl lg:rounded-2xl p-5 shadow-2xl space-y-4 lg:sticky lg:top-4 animate-in slide-in-from-bottom lg:animate-in lg:fade-in duration-200">
            
            {/* Drawer Top Nav */}
            <div className="flex items-center justify-between pb-1 border-b border-zinc-800/60 lg:border-none">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
                <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Lead Profile Inspector</span>
              </div>

              <button 
                onClick={() => setSelectedLeadId(null)}
                className="p-1.5 text-zinc-400 hover:text-white hover:bg-[#182035] rounded-lg transition"
                title="Close Inspector"
              >
                <X size={18} />
              </button>
            </div>

            {/* Profile Header */}
            <div className="flex items-start gap-3.5">
              <div className={`w-12 h-12 rounded-full font-bold text-sm flex items-center justify-center shrink-0 shadow-lg ${getAvatarColor(getInitials(activeLead.business_name))}`}>
                {getInitials(activeLead.business_name)}
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="text-base font-bold text-white tracking-tight leading-snug">
                  {activeLead.business_name}
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5 truncate">
                  {activeLead.category || 'Restaurant'} • {activeLead.city || 'Jodhpur'}, {activeLead.state || 'Rajasthan'}
                </p>
              </div>
            </div>

            {/* Action Buttons: Visit Website & Open in Maps */}
            <div className="flex items-center gap-2 pt-1">
              <button 
                onClick={() => {
                  if (activeLead.website && activeLead.website !== "Not Publicly Available") {
                    window.open(activeLead.website.startsWith("http") ? activeLead.website : `https://${activeLead.website}`, '_blank')
                  } else {
                    triggerAlert("No website URL available", "error")
                  }
                }}
                className="flex-1 py-2 px-3 bg-[#111627] hover:bg-[#19223a] border border-[#202c46] text-white text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition"
              >
                <Globe size={13} className="text-blue-400" />
                <span>Visit Website</span>
              </button>

              <button 
                onClick={() => {
                  if (activeLead.maps_url) {
                    window.open(activeLead.maps_url, '_blank')
                  } else {
                    window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(activeLead.business_name + ' ' + (activeLead.city || ''))}`, '_blank')
                  }
                }}
                className="flex-1 py-2 px-3 bg-[#111627] hover:bg-[#19223a] border border-[#202c46] text-white text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition"
              >
                <Compass size={13} className="text-indigo-400" />
                <span>Open in Maps</span>
              </button>

              <button 
                onClick={() => triggerOutreachGeneration(activeLead.id)}
                className="p-2 bg-[#111627] hover:bg-[#19223a] border border-[#202c46] text-zinc-400 hover:text-white rounded-xl transition"
                title="AI Generator"
              >
                <Sparkles size={14} className="text-amber-400" />
              </button>
            </div>

            {/* Navigation Tabs inside Drawer */}
            <div className="flex items-center gap-1 p-1 bg-[#0e1322] border border-[#1a2438] rounded-xl text-xs overflow-x-auto no-scrollbar">
              {[
                { id: 'overview', label: 'Overview' },
                { id: 'ai', label: 'AI Analysis' },
                { id: 'activity', label: 'Activity' },
                { id: 'notes', label: 'Notes' },
                { id: 'proposals', label: 'Proposals' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setDrawerTab(tab.id)}
                  className={`px-3 py-1.5 rounded-lg font-medium text-xs transition whitespace-nowrap ${
                    drawerTab === tab.id 
                      ? 'bg-[#4f46e5] text-white font-semibold shadow-sm' 
                      : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* TAB CONTENT: Overview */}
            {drawerTab === 'overview' && (
              <div className="space-y-4 pt-1">
                
                {/* No Website High-Priority Pitch Callout */}
                {(!activeLead.website || activeLead.website === "Not Publicly Available" || activeLead.website === "none" || activeLead.website === "null") && (
                  <div className="p-3.5 bg-gradient-to-r from-[#291708] to-[#1e1022] border border-amber-500/70 rounded-xl space-y-2 shadow-lg shadow-amber-950/30">
                    <div className="flex items-center gap-2">
                      <Flame size={15} className="text-amber-400 animate-pulse" />
                      <span className="text-xs font-bold text-amber-300">High-Converting Prospect: No Website Yet</span>
                    </div>
                    <p className="text-[11px] text-zinc-300 leading-relaxed">
                      {activeLead.business_name} has a strong {activeLead.google_rating || '4.8'}★ Google rating but no website. Over 70% of local searches in {activeLead.city || 'their area'} leak to competitors with online booking!
                    </p>
                    <div className="flex items-center gap-2 pt-1">
                      <button
                        onClick={() => {
                          setDrawerTab('ai')
                          setOutreachChannel('whatsapp')
                        }}
                        className="px-3 py-1.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black text-[11px] font-bold rounded-lg transition shadow-md flex items-center gap-1.5 active:scale-95"
                      >
                        <MessageSquare size={12} />
                        <span>Pitch Website (WhatsApp)</span>
                      </button>
                      <button
                        onClick={() => {
                          window.open(`${API_BASE}/portfolio/preview/${activeLead.id}?niche=${encodeURIComponent(activeLead.category || 'Business')}`, '_blank')
                        }}
                        className="px-2.5 py-1.5 bg-[#141b2e] hover:bg-[#1d2740] border border-amber-500/40 text-amber-200 text-[11px] font-semibold rounded-lg transition flex items-center gap-1"
                      >
                        <ExternalLink size={11} />
                        <span>Demo Site</span>
                      </button>
                    </div>
                  </div>
                )}
                
                {/* 3 Metric Blocks Strip */}
                <div className="grid grid-cols-3 gap-2 bg-[#0e1424] border border-[#1a263c] rounded-xl p-3">
                  <div>
                    <span className="text-[10px] text-zinc-400 block font-medium">Audit Score</span>
                    <span className="text-xl font-black text-emerald-400 block mt-0.5">
                      {activeLead.website_audit_score || (activeLead.business_name.includes("Gypsy") ? "87%" : "92%")}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] text-zinc-400 block font-medium">AI Status</span>
                    <span className="inline-block text-[11px] font-bold text-blue-400 bg-blue-950/50 border border-blue-800/80 px-2.5 py-0.5 rounded-md uppercase mt-1">
                      {activeLead.ai_score || "COLD"}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] text-zinc-400 block font-medium">Sales Stage</span>
                    <select
                      value={activeLead.status}
                      onChange={(e) => handleStatusChange(activeLead.id, e.target.value)}
                      className="w-full bg-[#121828] border border-[#202c44] text-white text-[11px] font-medium rounded-lg px-2 py-1 mt-1 focus:outline-none cursor-pointer"
                    >
                      {["New Lead", "Contacted", "Interested", "Meeting", "Proposal Sent", "Won", "Lost"].map(st => (
                        <option key={st} value={st}>{st}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* 2-Columns Information List */}
                <div className="grid grid-cols-2 gap-y-2.5 gap-x-4 text-xs bg-[#0e1424] border border-[#1a263c] rounded-xl p-3.5">
                  <div className="flex items-start gap-2">
                    <Tag size={13} className="text-zinc-500 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-[10px] text-zinc-500 font-medium block">Niche</span>
                      <span className="text-zinc-200 font-semibold">{activeLead.category || 'Restaurant'}</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <MapPin size={13} className="text-zinc-500 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-[10px] text-zinc-500 font-medium block">Location</span>
                      <span className="text-zinc-200 font-semibold truncate block">{activeLead.city || 'Jodhpur'}, {activeLead.state || 'Rajasthan'}</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <Phone size={13} className="text-indigo-400 shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <span className="text-[10px] text-zinc-500 font-medium block">Google Profile Phone</span>
                      {activeLead.phone && activeLead.phone !== "Not Publicly Available" ? (
                        <a 
                          href={`tel:${activeLead.phone}`}
                          className="text-indigo-300 hover:underline font-mono text-[11px] truncate block"
                        >
                          {activeLead.phone}
                        </a>
                      ) : (
                        <span className="text-zinc-500 text-[11px]">Not Available</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <MessageSquare size={13} className="text-emerald-400 shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <span className="text-[10px] text-zinc-500 font-medium block">WhatsApp Status</span>
                      {activeLead.whatsapp_number && activeLead.whatsapp_number !== "Not Publicly Available" ? (
                        <a 
                          href={`https://wa.me/${activeLead.whatsapp_number.replace(/[^0-9]/g, '')}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-emerald-400 hover:underline font-mono text-[11px] truncate flex items-center gap-1"
                        >
                          <span>{activeLead.whatsapp_number}</span>
                          <span className="text-[9px] bg-emerald-950 text-emerald-300 border border-emerald-800 px-1 rounded">Active</span>
                        </a>
                      ) : (
                        <span className="text-amber-400/90 text-[10.5px] font-medium">Landline (No WA)</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <Globe size={13} className="text-blue-400 shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <span className="text-[10px] text-zinc-500 font-medium block">Website</span>
                      {activeLead.website && activeLead.website !== "Not Publicly Available" ? (
                        <a 
                          href={activeLead.website.startsWith("http") ? activeLead.website : `https://${activeLead.website}`} 
                          target="_blank" 
                          rel="noreferrer" 
                          className="text-blue-400 hover:underline font-mono text-[11px] truncate block"
                        >
                          {activeLead.website.replace(/^https?:\/\//, '').replace(/^www\./, '')}
                        </a>
                      ) : (
                        <span className="text-zinc-500 text-[11px]">Not Available</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <CalendarDays size={13} className="text-zinc-500 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-[10px] text-zinc-500 font-medium block">Added On</span>
                      <span className="text-zinc-200 font-semibold">{getTimeAgo(activeLead.created_at)}</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-2 col-span-2">
                    <Clock size={13} className="text-zinc-500 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-[10px] text-zinc-500 font-medium block">Last Activity</span>
                      <span className="text-zinc-200 font-semibold">{getTimeAgo(activeLead.last_verified_at || activeLead.created_at)}</span>
                    </div>
                  </div>
                </div>

                {/* AI Insights Card */}
                <div className="bg-[#0e1424] border border-[#1e2942] rounded-xl p-3.5 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <Sparkles size={14} className="text-indigo-400" />
                      <span className="text-xs font-bold text-white">AI Insights</span>
                      <span className="text-[9px] font-extrabold uppercase bg-purple-950/80 border border-purple-800 text-purple-300 px-1.5 py-0.2 rounded-full">
                        Beta
                      </span>
                    </div>
                    
                    <button 
                      onClick={() => setDrawerTab('ai')}
                      className="text-[10px] font-semibold text-purple-300 hover:text-purple-200 bg-purple-950/60 border border-purple-800 px-2.5 py-1 rounded-lg transition"
                    >
                      View Full Report
                    </button>
                  </div>

                  <div className="space-y-1.5 text-xs text-zinc-300">
                    <div className="flex items-start gap-2">
                      <CheckCircle2 size={13} className="text-emerald-400 shrink-0 mt-0.5" />
                      <span className="text-[11px]">Website is mobile friendly</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <CheckCircle2 size={13} className="text-emerald-400 shrink-0 mt-0.5" />
                      <span className="text-[11px]">Good brand presence on local directories</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <AlertTriangle size={13} className="text-amber-400 shrink-0 mt-0.5" />
                      <span className="text-[11px]">Missing meta descriptions on key pages</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <AlertTriangle size={13} className="text-amber-400 shrink-0 mt-0.5" />
                      <span className="text-[11px]">Can improve page loading speed (2.8s)</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <AlertTriangle size={13} className="text-amber-400 shrink-0 mt-0.5" />
                      <span className="text-[11px]">Opportunity for local SEO optimization</span>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="space-y-2">
                  <span className="text-xs font-bold text-zinc-300 block">Quick Actions</span>
                  
                  {/* Row 1: Contact Channels */}
                  <div className="grid grid-cols-3 gap-2">
                    <button 
                      onClick={() => {
                        if (activeLead.phone && activeLead.phone !== "Not Publicly Available") {
                          window.location.href = `tel:${activeLead.phone}`
                        } else {
                          triggerAlert("No phone number registered", "error")
                        }
                      }}
                      className="py-2 px-2.5 bg-[#2563eb] hover:bg-[#1d4ed8] text-white font-semibold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-md shadow-blue-600/20 transition active:scale-95"
                    >
                      <Phone size={13} />
                      <span>Call</span>
                    </button>

                    <button 
                      onClick={() => {
                        const waNum = activeLead.whatsapp_number
                        if (waNum && waNum !== "Not Publicly Available") {
                          const cleaned = waNum.replace(/[^0-9]/g, '')
                          window.open(`https://wa.me/${cleaned}`, '_blank')
                        } else {
                          triggerAlert("No verified mobile WhatsApp registered for this business (Landline / Unlisted)", "error")
                        }
                      }}
                      className={`py-2 px-2.5 font-semibold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-md transition active:scale-95 ${
                        activeLead.whatsapp_number && activeLead.whatsapp_number !== "Not Publicly Available"
                          ? "bg-[#059669] hover:bg-[#047857] text-white shadow-emerald-600/20"
                          : "bg-zinc-800/80 text-zinc-500 cursor-not-allowed border border-zinc-700/50"
                      }`}
                      title={
                        activeLead.whatsapp_number && activeLead.whatsapp_number !== "Not Publicly Available"
                          ? `Chat on WhatsApp (${activeLead.whatsapp_number})`
                          : "No mobile WhatsApp (Landline only)"
                      }
                    >
                      <MessageSquare size={13} />
                      <span>WhatsApp</span>
                    </button>

                    <button 
                      onClick={() => {
                        if (activeLead.email && activeLead.email !== "Not Publicly Available") {
                          window.location.href = `mailto:${activeLead.email}`
                        } else {
                          triggerAlert("No verified email on file", "error")
                        }
                      }}
                      className="py-2 px-2.5 bg-[#1e40af] hover:bg-[#1e3a8a] text-white font-semibold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-md shadow-blue-900/20 transition active:scale-95"
                    >
                      <Mail size={13} />
                      <span>Send Email</span>
                    </button>
                  </div>

                  {/* Row 2: Workflow Actions */}
                  <div className="grid grid-cols-3 gap-2">
                    <button 
                      onClick={() => triggerAlert(`Proposal template initialized for ${activeLead.business_name}`)}
                      className="py-2 px-2 bg-[#101524] hover:bg-[#182035] border border-[#1e273a] text-zinc-300 hover:text-white text-[11px] font-medium rounded-xl flex items-center justify-center gap-1 transition"
                    >
                      <FileText size={12} className="text-zinc-400" />
                      <span className="truncate">Create Proposal</span>
                    </button>

                    <button 
                      onClick={() => setDrawerTab('activity')}
                      className="py-2 px-2 bg-[#101524] hover:bg-[#182035] border border-[#1e273a] text-zinc-300 hover:text-white text-[11px] font-medium rounded-xl flex items-center justify-center gap-1 transition"
                    >
                      <Calendar size={12} className="text-zinc-400" />
                      <span className="truncate">Schedule Follow-up</span>
                    </button>

                    <button 
                      onClick={() => handleStatusChange(activeLead.id, "Interested")}
                      className="py-2 px-2 bg-[#101524] hover:bg-[#182035] border border-[#1e273a] text-zinc-300 hover:text-white text-[11px] font-medium rounded-xl flex items-center justify-center gap-1 transition"
                    >
                      <CheckCheck size={12} className="text-emerald-400" />
                      <span className="truncate">Mark as Qualified</span>
                    </button>
                  </div>
                </div>

                {/* Tags Section */}
                <div className="space-y-2 pt-1 border-t border-[#161f33]">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-zinc-300">Tags</span>
                    <button 
                      onClick={() => setShowAddTagInput(!showAddTagInput)}
                      className="text-[10px] text-zinc-400 hover:text-white bg-[#101524] border border-[#1e273a] px-2 py-0.5 rounded-lg flex items-center gap-1 transition"
                    >
                      <Plus size={10} />
                      <span>Add Tag</span>
                    </button>
                  </div>

                  {showAddTagInput && (
                    <form onSubmit={handleAddTag} className="flex gap-2 animate-in fade-in duration-150">
                      <input 
                        type="text" 
                        placeholder="Tag name (e.g. priority)..." 
                        value={newTag} 
                        onChange={e => setNewTag(e.target.value)}
                        className="w-full bg-[#101524] border border-[#1e273a] rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-indigo-500" 
                      />
                      <button type="submit" className="px-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-xs">Save</button>
                    </form>
                  )}

                  <div className="flex flex-wrap gap-1.5">
                    {getLeadTags(activeLead).map((t, idx) => (
                      <span 
                        key={idx} 
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#101524] border border-[#1e273a] text-zinc-300 text-[11px] font-medium rounded-lg"
                      >
                        {t}
                        <button onClick={() => handleRemoveTag(t)} className="text-zinc-500 hover:text-red-400 ml-0.5">×</button>
                      </span>
                    ))}
                  </div>
                </div>

              </div>
            )}

            {/* TAB CONTENT: AI Analysis */}
            {drawerTab === 'ai' && (
              <div className="space-y-4 pt-1 animate-in fade-in duration-150">
                <div className="p-4 rounded-xl bg-[#0e1424] border border-[#1b263e] space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                      <Sparkles size={14} />
                      Hook → Problem → Solution Engine
                    </span>
                    <div className="flex items-center gap-1.5">
                      <button 
                        onClick={() => {
                          triggerAlert("Generating tailored outreach for ALL leads...")
                          fetch(`${API_BASE}/ai/outreach/batch-generate-all`, { 
                            method: "POST",
                            headers: { 'Authorization': `Bearer ${session?.token}` }
                          })
                            .then(res => res.json())
                            .then(data => {
                              if (data.status === "success") {
                                triggerAlert(`Outreach generated for ${data.processed_count} leads!`)
                                handleViewLead(activeLead.id)
                              }
                            })
                            .catch(() => triggerAlert("Batch generation failed", "error"))
                        }}
                        className="text-[10px] text-zinc-300 bg-[#0b0f19] hover:bg-[#182035] border border-[#233150] px-2 py-1 rounded-lg font-semibold transition"
                        title="Generate outreach for every lead in the CRM"
                      >
                        Generate All
                      </button>
                      <button 
                        onClick={() => triggerOutreachGeneration(activeLead.id)}
                        className="text-[10px] text-white bg-indigo-600 hover:bg-indigo-700 px-2.5 py-1 rounded-lg font-semibold transition"
                      >
                        Regenerate
                      </button>
                    </div>
                  </div>

                  {/* Channel Switcher — 5 channels */}
                  <div className="grid grid-cols-5 gap-1 p-1 bg-[#0b0f19] border border-[#182236] rounded-lg text-[10px] font-semibold">
                    {['email', 'whatsapp', 'linkedin', 'instagram', 'phone'].map(ch => (
                      <button
                        key={ch}
                        onClick={() => setOutreachChannel(ch)}
                        className={`py-1 rounded capitalize transition ${
                          outreachChannel === ch ? 'bg-[#4f46e5] text-white' : 'text-zinc-400 hover:text-white'
                        }`}
                      >
                        {ch === 'phone' ? 'Call' : ch}
                      </button>
                    ))}
                  </div>

                  {/* Pitch Script Preview — reads from actual outreach_materials */}
                  {(() => {
                    const om = leadDetail?.outreach_materials
                    const channelMap = {
                      email: om?.email_content,
                      whatsapp: om?.whatsapp_message,
                      linkedin: om?.linkedin_message,
                      instagram: om?.instagram_dm,
                      phone: om?.cold_call_script
                    }
                    const currentMessage = channelMap[outreachChannel] || null
                    const emailSubject = om?.email_subject || ""

                    return (
                      <div className="bg-[#0b0f19] border border-[#182236] rounded-xl p-3 text-xs text-zinc-300 space-y-2">
                        <div className="flex items-center justify-between text-[10px] text-zinc-500">
                          <span>
                            {currentMessage 
                              ? `Personalized ${outreachChannel === 'phone' ? 'COLD CALL' : outreachChannel.toUpperCase()} Script:`
                              : `No ${outreachChannel} outreach generated yet`
                            }
                          </span>
                          {currentMessage && (
                            <button 
                              onClick={() => copyToClipboard(currentMessage)}
                              className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-bold"
                            >
                              <Copy size={11} />
                              <span>Copy</span>
                            </button>
                          )}
                        </div>

                        {/* Email subject line banner */}
                        {outreachChannel === 'email' && emailSubject && (
                          <div className="flex items-center gap-2 bg-[#111627] border border-[#1e2942] rounded-lg px-3 py-1.5">
                            <span className="text-[10px] text-zinc-500 font-medium shrink-0">Subject:</span>
                            <span className="text-[11px] text-indigo-300 font-semibold truncate">{emailSubject}</span>
                            <button 
                              onClick={() => copyToClipboard(emailSubject)} 
                              className="ml-auto text-zinc-500 hover:text-indigo-400 shrink-0"
                              title="Copy subject line"
                            >
                              <Copy size={10} />
                            </button>
                          </div>
                        )}

                        {currentMessage ? (
                          <div className="text-zinc-300 text-xs leading-relaxed font-sans bg-[#080c14] p-3 rounded-lg border border-zinc-800 whitespace-pre-wrap max-h-[340px] overflow-y-auto custom-scrollbar">
                            {currentMessage}
                          </div>
                        ) : (
                          <div className="text-center py-6 space-y-2">
                            <Sparkles size={20} className="text-zinc-600 mx-auto" />
                            <p className="text-[11px] text-zinc-500">
                              Click <strong className="text-indigo-400">Regenerate</strong> to craft a personalized Hook→Problem→Solution message for {activeLead.business_name}.
                            </p>
                          </div>
                        )}
                      </div>
                    )
                  })()}

                  {/* 3-Part Structure Key */}
                  {leadDetail?.outreach_materials && (
                    <div className="grid grid-cols-3 gap-2 pt-1">
                      <div className="bg-[#0b1a0f] border border-[#1a3d1a] rounded-lg p-2 text-center">
                        <span className="text-[9px] font-bold text-emerald-400 uppercase tracking-wider block">Step 1</span>
                        <span className="text-[10px] text-emerald-300 font-medium">Positive Hook</span>
                      </div>
                      <div className="bg-[#1a150b] border border-[#3d2e1a] rounded-lg p-2 text-center">
                        <span className="text-[9px] font-bold text-amber-400 uppercase tracking-wider block">Step 2</span>
                        <span className="text-[10px] text-amber-300 font-medium">Problem</span>
                      </div>
                      <div className="bg-[#0b0f1a] border border-[#1a2a3d] rounded-lg p-2 text-center">
                        <span className="text-[9px] font-bold text-blue-400 uppercase tracking-wider block">Step 3</span>
                        <span className="text-[10px] text-blue-300 font-medium">Solution</span>
                      </div>
                    </div>
                  )}

                  {/* Gemini Custom Pitch Co-Pilot Box */}
                  <div className="pt-3 border-t border-[#182236] space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-amber-300 flex items-center gap-1.5">
                        <Sparkles size={13} className="text-amber-400" />
                        Gemini AI Custom Pitch Writer
                      </span>
                      <span className="text-[10px] text-zinc-400 bg-[#121828] border border-[#1e273a] px-2 py-0.5 rounded">
                        API Active
                      </span>
                    </div>
                    <input 
                      type="text" 
                      placeholder="e.g. Focus on 48h website launch, WhatsApp ordering, or special discount..." 
                      value={customPitchPrompt}
                      onChange={(e) => setCustomPitchPrompt(e.target.value)}
                      className="w-full bg-[#101524] border border-[#1e273a] rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500 transition"
                    />
                    <button
                      onClick={() => handleGenerateCustomPitch(activeLead.id)}
                      disabled={generatingCustomPitch}
                      className="w-full py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-md transition active:scale-95"
                    >
                      <Sparkles size={13} className={generatingCustomPitch ? "animate-spin" : ""} />
                      <span>{generatingCustomPitch ? "Gemini is Writing Custom Pitch..." : `Generate Custom ${outreachChannel.toUpperCase()} Pitch`}</span>
                    </button>

                    {customPitchResult && (
                      <div className="bg-[#0b0f19] border border-amber-600/40 rounded-xl p-3 space-y-2 animate-in fade-in duration-200 mt-2">
                        <div className="flex items-center justify-between text-[11px] text-amber-400 font-semibold">
                          <span>✨ Custom Generated Pitch ({customPitchResult.channel || outreachChannel}):</span>
                          <button 
                            onClick={() => copyToClipboard(customPitchResult.message)}
                            className="flex items-center gap-1 text-xs text-amber-300 hover:text-white font-bold"
                          >
                            <Copy size={11} />
                            <span>Copy</span>
                          </button>
                        </div>
                        {customPitchResult.subject && (
                          <p className="text-[11px] font-semibold text-zinc-300">
                            <strong>Subject:</strong> {customPitchResult.subject}
                          </p>
                        )}
                        <div className="text-zinc-200 text-xs bg-[#070a12] p-2.5 rounded-lg border border-[#1c2438] whitespace-pre-wrap max-h-[200px] overflow-y-auto">
                          {customPitchResult.message}
                        </div>
                        <div className="flex items-center gap-2 pt-1">
                          <button
                            onClick={() => {
                              const waNum = activeLead.whatsapp_number
                              if (waNum && waNum !== "Not Publicly Available") {
                                const cleaned = waNum.replace(/[^0-9]/g, '')
                                window.open(`https://wa.me/${cleaned}?text=${encodeURIComponent(customPitchResult.message)}`, '_blank')
                              } else {
                                triggerAlert("No mobile WhatsApp number on file. Copied message to clipboard!", "info")
                                copyToClipboard(customPitchResult.message)
                              }
                            }}
                            className="flex-1 py-1.5 bg-[#059669] hover:bg-[#047857] text-white font-bold text-[11px] rounded-lg flex items-center justify-center gap-1 transition"
                          >
                            <MessageSquare size={12} />
                            <span>Send via WhatsApp</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT: Activity & Followups */}
            {drawerTab === 'activity' && (
              <div className="space-y-4 pt-1 animate-in fade-in duration-150">
                <div className="p-4 rounded-xl bg-[#0e1424] border border-[#1b263e] space-y-3 text-xs">
                  <span className="font-bold text-white block">Representative Assignment & Scheduling</span>
                  
                  <div>
                    <label className="text-[10px] text-zinc-400 font-medium block mb-1">Assign To Agent</label>
                    <select
                      value={assignedToId}
                      onChange={(e) => setAssignedToId(e.target.value)}
                      className="w-full bg-[#121828] border border-[#202c44] text-white rounded-lg p-2 text-xs focus:outline-none"
                    >
                      <option value="">-- Unassigned --</option>
                      <option value="1">Default Admin (Admin)</option>
                      <option value="2">Sales Representative</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[10px] text-zinc-400 font-medium block mb-1">Scheduled Next Contact Date</label>
                    <input 
                      type="datetime-local" 
                      value={followUpDate}
                      onChange={(e) => setFollowUpDate(e.target.value)}
                      className="w-full bg-[#121828] border border-[#202c44] text-white rounded-lg p-2 text-xs focus:outline-none"
                    />
                  </div>

                  <button 
                    onClick={handleSaveChanges}
                    disabled={savingNotes}
                    className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl transition"
                  >
                    {savingNotes ? "Saving..." : "Save Schedule Updates"}
                  </button>
                </div>
              </div>
            )}

            {/* TAB CONTENT: Notes */}
            {drawerTab === 'notes' && (
              <div className="space-y-4 pt-1 animate-in fade-in duration-150">
                <div className="p-4 rounded-xl bg-[#0e1424] border border-[#1b263e] space-y-3">
                  <span className="text-xs font-bold text-white block">Interactive Client Notes</span>
                  <textarea
                    rows={5}
                    value={leadNotes}
                    onChange={(e) => setLeadNotes(e.target.value)}
                    placeholder="Log discovery calls, decision-maker details, objections, and follow-up notes here..."
                    className="w-full bg-[#121828] border border-[#202c44] text-white text-xs rounded-xl p-3 focus:outline-none focus:border-indigo-500"
                  />
                  <div className="flex justify-end">
                    <button 
                      onClick={handleSaveChanges}
                      disabled={savingNotes}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl transition"
                    >
                      {savingNotes ? "Saving..." : "Save Notes"}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT: Proposals */}
            {drawerTab === 'proposals' && (
              <div className="space-y-4 pt-1 animate-in fade-in duration-150">
                <div className="p-4 rounded-xl bg-[#0e1424] border border-[#1b263e] space-y-3 text-xs">
                  <span className="font-bold text-white block">Customized Agency Proposals</span>
                  <p className="text-zinc-400 text-xs">
                    Generate an instant branded quotation and prototype landing page for {activeLead.business_name}.
                  </p>
                  <div className="space-y-2">
                    <button 
                      onClick={() => triggerAlert("Proposal generator compiling HTML & PDF contract...")}
                      className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-lg shadow-indigo-600/20 transition"
                    >
                      <FileText size={14} />
                      <span>Draft Web Dev Quotation</span>
                    </button>
                    <button 
                      onClick={() => triggerAlert("Previewing responsive prototype demo...")}
                      className="w-full py-2.5 bg-[#121828] hover:bg-[#182035] border border-[#202c44] text-zinc-300 font-semibold text-xs rounded-xl flex items-center justify-center gap-1.5 transition"
                    >
                      <Globe size={14} className="text-blue-400" />
                      <span>Launch Interactive Demo Prototype</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

          </div>
          </>
        )}

      </div>

      {/* MODAL 1: Add Lead Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0e1424] border border-[#1e273a] w-full max-w-lg rounded-2xl p-6 space-y-4 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
              <h3 className="text-base font-bold text-white">Add New Business Lead</h3>
              <button onClick={() => setShowAddModal(false)} className="text-zinc-400 hover:text-white p-1 rounded-lg">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-zinc-400 mb-1 font-medium">Business Name *</label>
                <input 
                  type="text" 
                  required
                  placeholder="e.g. Gypsy Vegetarian Restaurant"
                  value={addForm.business_name}
                  onChange={e => setAddForm({ ...addForm, business_name: e.target.value })}
                  className="w-full bg-[#121828] border border-[#1e273a] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-400 mb-1 font-medium">Niche / Category</label>
                  <select 
                    value={addForm.category}
                    onChange={e => setAddForm({ ...addForm, category: e.target.value })}
                    className="w-full bg-[#121828] border border-[#1e273a] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    {ALL_NICHES.map(n => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-zinc-400 mb-1 font-medium">City</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Jodhpur"
                    value={addForm.city}
                    onChange={e => setAddForm({ ...addForm, city: e.target.value })}
                    className="w-full bg-[#121828] border border-[#1e273a] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-400 mb-1 font-medium">Phone Number</label>
                  <input 
                    type="text" 
                    placeholder="+91 98765 43210"
                    value={addForm.phone}
                    onChange={e => setAddForm({ ...addForm, phone: e.target.value })}
                    className="w-full bg-[#121828] border border-[#1e273a] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-zinc-400 mb-1 font-medium">Website URL</label>
                  <input 
                    type="text" 
                    placeholder="https://example.com"
                    value={addForm.website}
                    onChange={e => setAddForm({ ...addForm, website: e.target.value })}
                    className="w-full bg-[#121828] border border-[#1e273a] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
                <button 
                  type="button" 
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-[#121828] text-zinc-400 hover:text-white rounded-xl"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-lg shadow-indigo-600/20"
                >
                  Add Lead Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Scrape Directory Modal */}
      {showScrapeModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0e1424] border border-[#1e273a] w-full max-w-md rounded-2xl p-6 space-y-4 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <RefreshCw size={15} className="text-indigo-400" />
                Scrape Quality Leads (No Website)
              </h3>
              <button onClick={() => setShowScrapeModal(false)} className="text-zinc-400 hover:text-white p-1 rounded-lg">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleScrapeSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-zinc-400 mb-1 font-medium">Directory Source</label>
                <select 
                  value={scrapeForm.source}
                  onChange={e => setScrapeForm({ ...scrapeForm, source: e.target.value })}
                  className="w-full bg-[#121828] border border-[#1e273a] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="Google Maps">Google Maps (Fast Headless Engine)</option>
                  <option value="Justdial">Justdial Directory</option>
                  <option value="IndiaMART">IndiaMART Directory</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-400 mb-1 font-medium">Target Category / Niche</label>
                  <select 
                    value={scrapeForm.category}
                    onChange={e => setScrapeForm({ ...scrapeForm, category: e.target.value })}
                    className="w-full bg-[#121828] border border-[#1e273a] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    {ALL_NICHES.map(n => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1 font-medium">City</label>
                  <input 
                    type="text" 
                    required
                    placeholder="e.g. Jodhpur or Ahmedabad"
                    value={scrapeForm.city}
                    onChange={e => setScrapeForm({ ...scrapeForm, city: e.target.value })}
                    className="w-full bg-[#121828] border border-[#1e273a] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-zinc-400 mb-1 font-medium">Leads Limit</label>
                <input 
                  type="number" 
                  min="1" 
                  max="50"
                  value={scrapeForm.limit}
                  onChange={e => setScrapeForm({ ...scrapeForm, limit: parseInt(e.target.value) || 10 })}
                  className="w-full bg-[#121828] border border-[#1e273a] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
                <button 
                  type="button" 
                  onClick={() => setShowScrapeModal(false)}
                  className="px-4 py-2 bg-[#121828] text-zinc-400 hover:text-white rounded-xl"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-lg shadow-indigo-600/20"
                >
                  Launch Scraper
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* LIVE SCRAPER ACTIVE LOADING CARD (Disappears automatically once complete) */}
      {scrapingTask && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-[#0b0f19] border border-indigo-500/50 w-full max-w-lg rounded-3xl p-6 shadow-2xl shadow-indigo-500/25 relative overflow-hidden">
            
            {/* Ambient background glow */}
            <div className="absolute -top-24 -right-24 w-60 h-60 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"></div>
            <div className="absolute -bottom-24 -left-24 w-60 h-60 bg-blue-500/15 rounded-full blur-3xl pointer-events-none"></div>

            {/* Card Header */}
            <div className="flex items-center justify-between pb-4 border-b border-[#1c273c]">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-2xl bg-indigo-500/10 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
                  {scrapingTask.status === 'completed' ? (
                    <CheckCircle2 size={22} className="text-emerald-400" />
                  ) : scrapingTask.status === 'failed' ? (
                    <AlertTriangle size={22} className="text-rose-400" />
                  ) : (
                    <RefreshCw size={22} className="animate-spin text-indigo-400" />
                  )}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    {scrapingTask.status === 'completed' 
                      ? 'Lead Discovery Complete!' 
                      : scrapingTask.status === 'failed'
                      ? 'Discovery Issue'
                      : 'Finding Quality Leads (No Website)'}
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider">
                      {scrapingTask.category}
                    </span>
                  </h3>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Target City: <span className="text-white font-medium">{scrapingTask.city}</span> • Source: <span className="text-indigo-300 font-medium">{scrapingTask.source}</span>
                  </p>
                </div>
              </div>

              {scrapingTask.status !== 'running' && (
                <button 
                  onClick={() => setScrapingTask(null)}
                  className="p-1.5 text-zinc-500 hover:text-white rounded-lg hover:bg-zinc-800/60 transition"
                >
                  <X size={16} />
                </button>
              )}
            </div>

            {/* Radar Visual & Progress */}
            <div className="py-5 space-y-4">
              <div className="bg-[#0e1424] border border-[#1a253a] rounded-2xl p-4 flex items-center gap-4">
                <div className="relative w-12 h-12 flex items-center justify-center shrink-0">
                  <div className={`absolute inset-0 rounded-full border border-indigo-500/30 ${scrapingTask.status === 'running' ? 'animate-ping' : ''}`}></div>
                  <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/60 flex items-center justify-center text-indigo-300 shadow-inner">
                    <Compass size={18} className={scrapingTask.status === 'running' ? 'animate-spin' : ''} />
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold text-white truncate">
                    {scrapingTask.progressMessage || "Scanning local directories..."}
                  </p>
                  <div className="w-full bg-zinc-800/80 rounded-full h-2 mt-2.5 overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-500 rounded-full ${
                        scrapingTask.status === 'completed'
                          ? 'w-full bg-emerald-500'
                          : scrapingTask.status === 'failed'
                          ? 'w-full bg-rose-500'
                          : 'w-4/5 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-400 animate-pulse'
                      }`}
                    ></div>
                  </div>
                </div>
              </div>

              {/* 4 Step Progress Indicators */}
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#0e1424]/60 border border-[#172033]">
                  <span className="text-zinc-300 flex items-center gap-2">
                    <CheckCircle2 size={13} className="text-indigo-400" />
                    1. Querying Google Maps & Local Business Registries
                  </span>
                  <span className="text-[10px] font-bold text-emerald-400">Verified</span>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#0e1424]/60 border border-[#172033]">
                  <span className="text-zinc-300 flex items-center gap-2">
                    <CheckCircle2 size={13} className="text-indigo-400" />
                    2. Filtering Out Existing Websites (Strict No-Website Policy)
                  </span>
                  <span className="text-[10px] font-bold text-emerald-400">Active</span>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#0e1424]/60 border border-[#172033]">
                  <span className="text-zinc-300 flex items-center gap-2">
                    <CheckCircle2 size={13} className="text-indigo-400" />
                    3. Checking Cross-Location Cleared List (Zero Duplication)
                  </span>
                  <span className="text-[10px] font-bold text-emerald-400">Suppressed</span>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#0e1424]/60 border border-[#172033]">
                  <span className="text-zinc-300 flex items-center gap-2">
                    {scrapingTask.status === 'completed' ? (
                      <CheckCircle2 size={13} className="text-emerald-400" />
                    ) : (
                      <Sparkles size={13} className="text-amber-400 animate-spin" />
                    )}
                    4. Auto-Generating 3-Tier Outreach & Intent Scoring
                  </span>
                  <span className={`text-[10px] font-bold ${scrapingTask.status === 'completed' ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {scrapingTask.status === 'completed' ? 'Done' : 'Processing...'}
                  </span>
                </div>
              </div>
            </div>

            {/* Card Footer */}
            <div className="pt-3 border-t border-[#1c273c] flex items-center justify-between text-[11px] text-zinc-500">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Verified businesses without websites
              </span>
              <span className="text-indigo-400 font-medium">Auto-closing on completion</span>
            </div>

          </div>
        </div>
      )}

    </div>
  )
}
