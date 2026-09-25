import React, { useState, useEffect } from 'react'
import { FileText, Plus, Trash, ExternalLink, RefreshCw, FileCheck, CircleDollarSign } from 'lucide-react'

export default function ProposalsView({ API_BASE, triggerAlert }) {
  const [leads, setLeads] = useState([])
  const [selectedLeadId, setSelectedLeadId] = useState("")
  const [docType, setDocType] = useState("PROPOSAL")
  const [title, setTitle] = useState("")
  
  // Custom Line items
  const [items, setItems] = useState([])
  const [newItem, setNewItem] = useState({ description: "", details: "", price: "" })
  
  // Recent documents list
  const [recentDocs, setRecentDocs] = useState([])
  const [loadingDocs, setLoadingDocs] = useState(false)

  useEffect(() => {
    // Fetch all leads to populate dropdown selector
    fetch(`${API_BASE}/leads/?limit=100`)
      .then(res => res.json())
      .then(data => {
        setLeads(data.leads || [])
        if (data.leads && data.leads.length > 0) {
          setSelectedLeadId(data.leads[0].id)
        }
      })
      .catch(err => console.error("Error loading leads list:", err))
  }, [])

  useEffect(() => {
    if (selectedLeadId) {
      loadLeadDocuments(selectedLeadId)
    }
  }, [selectedLeadId])

  const loadLeadDocuments = (leadId) => {
    setLoadingDocs(true)
    fetch(`${API_BASE}/proposals/lead/${leadId}`)
      .then(res => res.json())
      .then(data => {
        setRecentDocs(data || [])
        setLoadingDocs(false)
      })
      .catch(err => {
        console.error("Error loading lead documents:", err)
        setLoadingDocs(false)
      })
  }

  // Prepopulate standard pricing structures depending on document type
  const loadPreconfiguredScope = () => {
    if (docType === "PROPOSAL" || docType === "QUOTATION") {
      setItems([
        { description: "Mobile-Responsive UI/UX Redesign", details: "Redesigning layout structures using standard CSS grids and flexbox.", price: 15000 },
        { description: "SSL Certificate & HTTPS Setup", details: "Installation, securing browser transport protocol headers.", price: 3000 },
        { description: "Lead Form & CRM Automations Integration", details: "Interactive forms to direct customer registrations straight to dashboard database.", price: 4000 }
      ])
      setTitle("Custom Business Website Rebuild")
    } else if (docType === "INVOICE") {
      setItems([
        { description: "Website Optimization Project - Initial Advance Mobilization", details: "50% project cost retainer.", price: 11000 }
      ])
      setTitle("Advance Mobilization Invoice")
    } else {
      setItems([
        { description: "Design, Development & Optimization SLA", details: "Comprehensive design and local search engine optimizations.", price: 22000 }
      ])
      setTitle("Custom Service Agreement Contract")
    }
    triggerAlert("Standard project pricing items loaded!")
  }

  // Add line item
  const handleAddItem = (e) => {
    e.preventDefault()
    if (!newItem.description || !newItem.price) {
      triggerAlert("Description and Price are required fields", "error")
      return
    }
    setItems([...items, {
      description: newItem.description,
      details: newItem.details,
      price: parseFloat(newItem.price)
    }])
    setNewItem({ description: "", details: "", price: "" })
  }

  const handleDeleteItem = (index) => {
    setItems(items.filter((_, idx) => idx !== index))
  }

  // Math totals
  const subtotal = items.reduce((acc, curr) => acc + curr.price, 0)
  const tax = Math.round(subtotal * 0.18)
  const total = subtotal + tax

  // Generate Document
  const handleGenerate = () => {
    if (items.length === 0) {
      triggerAlert("Add at least one line item to continue", "error")
      return
    }
    
    const payload = {
      lead_id: parseInt(selectedLeadId),
      doc_type: docType,
      title: title || `${docType.toLowerCase().replace(/^\w/, c => c.toUpperCase())} details`,
      items: items
    }

    fetch(`${API_BASE}/proposals/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          triggerAlert(`${docType} compiled successfully!`)
          loadLeadDocuments(selectedLeadId)
        }
      })
      .catch(err => {
        console.error("Document compilation error:", err)
        triggerAlert("Failed to generate document", "error")
      })
  }

  // Update proposal status (which changes CRM lead status)
  const handleDocStatusChange = (docId, newStatus) => {
    fetch(`${API_BASE}/proposals/${docId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    })
      .then(res => res.json())
      .then(() => {
        triggerAlert(`Document status changed to ${newStatus}`)
        setRecentDocs(recentDocs.map(d => d.id === docId ? { ...d, status: newStatus } : d))
      })
      .catch(err => console.error("Error setting status:", err))
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      {/* Left Columns: Config and Builder */}
      <div className="lg:col-span-2 space-y-6">
        
        {/* Settings wrapper */}
        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 space-y-5">
          <h3 className="text-sm font-bold text-white tracking-wide uppercase">Document Builder Engine</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-zinc-500 font-bold mb-1">Select Client Target</label>
              <select
                value={selectedLeadId}
                onChange={(e) => setSelectedLeadId(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-white focus:outline-none"
              >
                <option value="" disabled>Choose Lead...</option>
                {leads.map(l => (
                  <option key={l.id} value={l.id}>{l.business_name} ({l.city})</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-zinc-500 font-bold mb-1">Document Format</label>
              <div className="flex gap-2">
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-white focus:outline-none"
                >
                  <option value="PROPOSAL">Project Proposal</option>
                  <option value="QUOTATION">Quotation Invoice</option>
                  <option value="INVOICE">Tax Invoice Bill</option>
                  <option value="CONTRACT">SLA Service Agreement</option>
                </select>
                <button
                  type="button"
                  onClick={loadPreconfiguredScope}
                  className="px-3 sm:px-4 bg-zinc-950 hover:bg-zinc-900 border border-zinc-800 rounded-xl text-indigo-400 font-bold text-xs transition whitespace-nowrap"
                >
                  Load Template
                </button>
              </div>
            </div>
          </div>

          <div className="text-xs">
            <label className="block text-zinc-500 font-bold mb-1">Display Scope Title</label>
            <input
              type="text"
              placeholder="e.g. Modern Mobile Rebuild & HTTPS Security Setup"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-white focus:outline-none"
            />
          </div>
        </div>

        {/* Adding Pricing Line Items */}
        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 space-y-5">
          <h3 className="text-sm font-bold text-white tracking-wide uppercase">Scope pricing & line items</h3>

          {/* Table display of current items */}
          {items.length === 0 ? (
            <div className="text-center py-6 text-xs text-zinc-500 border border-dashed border-zinc-800 rounded-xl">
              No pricing items added yet. Click 'Load Template' above or use the form below.
            </div>
          ) : (
            <div className="border border-zinc-800 rounded-xl overflow-x-auto text-xs">
              <table className="w-full text-left min-w-[340px]">
                <thead>
                  <tr className="bg-zinc-950 text-zinc-500 text-[10px] font-bold uppercase border-b border-zinc-800">
                    <th className="p-3 pl-4">Description</th>
                    <th className="p-3 text-right">Price</th>
                    <th className="p-3 text-center">Delete</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item, idx) => (
                    <tr key={idx} className="border-b border-zinc-800/40 hover:bg-zinc-900/10">
                      <td className="p-3 pl-4">
                        <span className="font-semibold text-white block">{item.description}</span>
                        <span className="text-[10px] text-zinc-500 block">{item.details}</span>
                      </td>
                      <td className="p-3 text-right font-medium">₹{item.price.toLocaleString('en-IN')}</td>
                      <td className="p-3 text-center">
                        <button onClick={() => handleDeleteItem(idx)} className="text-red-400 hover:text-red-300">
                          <Trash className="w-3.5 h-3.5 mx-auto" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Form to insert item */}
          <form onSubmit={handleAddItem} className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end text-xs">
            <div className="sm:col-span-2">
              <input
                type="text"
                placeholder="Item Label (e.g. SSL Security Integration)"
                required
                value={newItem.description}
                onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-white"
              />
            </div>
            <div>
              <input
                type="number"
                placeholder="Price (INR)"
                required
                value={newItem.price}
                onChange={(e) => setNewItem({ ...newItem, price: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-white"
              />
            </div>
            <button
              type="submit"
              className="py-2.5 bg-zinc-900 border border-zinc-800 hover:border-indigo-500 text-white font-bold rounded-lg flex items-center justify-center gap-1.5 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Item</span>
            </button>
          </form>
        </div>

      </div>

      {/* Right Column: Checkout Summary & Documents Lists */}
      <div className="space-y-6">
        
        {/* Math checker card */}
        <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 space-y-4">
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide">Financial breakdown</span>
          
          <div className="space-y-2.5 text-xs text-zinc-400">
            <div className="flex justify-between">
              <span>Subtotal:</span>
              <span className="text-white font-semibold">₹{subtotal.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between">
              <span>GST Tax (18%):</span>
              <span className="text-white font-semibold">₹{tax.toLocaleString('en-IN')}</span>
            </div>
            <div className="border-t border-zinc-800/80 pt-3 flex justify-between text-sm font-bold text-white">
              <span>Total Invoice Amount:</span>
              <span className="text-indigo-400">₹{total.toLocaleString('en-IN')}</span>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={items.length === 0}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl hover:shadow-lg hover:shadow-indigo-600/10 transition mt-2"
          >
            Compile professional {docType}
          </button>
        </div>

        {/* List of files generated */}
        <div className="p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 space-y-4">
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide block">Recent documents</span>

          {loadingDocs ? (
            <div className="flex items-center justify-center py-6">
              <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : recentDocs.length === 0 ? (
            <p className="text-[11px] text-zinc-500 text-center py-4">No documents created for this lead yet.</p>
          ) : (
            <div className="space-y-3">
              {recentDocs.map(doc => (
                <div key={doc.id} className="p-4 bg-zinc-950 border border-zinc-850 rounded-xl space-y-3">
                  <div className="flex justify-between items-start">
                    <div className="min-w-0">
                      <span className="font-bold text-white text-xs block truncate">{doc.title}</span>
                      <span className="text-[10px] text-zinc-500 block uppercase font-bold tracking-wider mt-0.5">{doc.proposal_type}</span>
                    </div>
                    <a
                      href={`${API_BASE.replace(/\/api\/?$/, '')}${doc.file_path}`}
                      target="_blank"
                      rel="noreferrer"
                      className="p-1 rounded bg-zinc-900 hover:bg-zinc-800 text-indigo-400 hover:text-indigo-300"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                  
                  <div className="flex items-center justify-between border-t border-zinc-900/50 pt-2.5 text-[10px] text-zinc-500">
                    <span>Date: {new Date(doc.created_at).toLocaleDateString()}</span>
                    <select
                      value={doc.status}
                      onChange={(e) => handleDocStatusChange(doc.id, e.target.value)}
                      className={`bg-zinc-900 border border-zinc-800 rounded px-1.5 py-0.5 outline-none font-bold ${
                        doc.status === 'Accepted' ? 'text-emerald-400' : (doc.status === 'Declined' ? 'text-red-400' : 'text-zinc-400')
                      }`}
                    >
                      <option>Draft</option>
                      <option>Sent</option>
                      <option>Accepted</option>
                      <option>Declined</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

    </div>
  )
}
