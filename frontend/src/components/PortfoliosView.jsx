import React, { useState, useEffect } from 'react'
import { Briefcase, Eye, Link, Copy, Check, Info, LayoutTemplate } from 'lucide-react'

export default function PortfoliosView({ API_BASE, triggerAlert }) {
  const [leads, setLeads] = useState([])
  const [selectedLeadId, setSelectedLeadId] = useState("")
  const [activePrototypes, setActivePrototypes] = useState({}) // maps niche -> url

  const niches = [
    {
      id: "Restaurant",
      title: "Gourmet Bistro & Menu Portal",
      desc: "Styled for fine dining and cafes. Includes menu highlights, table booking reservation form, and map location embeds.",
      features: ["Table Reservations", "Online Menu Grid", "Google Maps Location", "Review Rating Cards"],
      icon: "🍝",
      image: "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=600"
    },
    {
      id: "Gym",
      title: "Strength & Conditioning Fitness Hub",
      desc: "Dark active theme designed for gyms, MMA clubs, or crossfit studios. Features price tables and trial voucher capture forms.",
      features: ["Membership Tier Matrix", "Class Schedules", "Personal Coach Profiles", "Free Trial Pass Capture"],
      icon: "🏋️",
      image: "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=600"
    },
    {
      id: "Salon",
      title: "Premium Styling & Spa Lounge",
      desc: "Elegant aesthetics with dark rose gold accents. Suitable for barber shops, beauty salons, and massage therapists.",
      features: ["Stylist Bios", "Service Rate Book", "Appointment Slots", "WhatsApp Quick Launch"],
      icon: "✂️",
      image: "https://images.unsplash.com/photo-1560066984-138dadb4c035?q=80&w=600"
    },
    {
      id: "Dentist",
      title: "Family Dental Clinic & Smile Care",
      desc: "Clean light medical styling with blue accents. Features patient advice forms, tooth specialty guides, and dental consult schedules.",
      features: ["Laser Treatment Guides", "Painless Treatment Demos", "Specialist Doctor Profiles", "Request Consultation Form"],
      icon: "🦷",
      image: "https://images.unsplash.com/photo-1629909613654-28e377c37b09?q=80&w=600"
    },
    {
      id: "Clinic",
      title: "Apex Medical & Health Center",
      desc: "Clear white-emerald styling for general clinics, physiotherapists, or pediatric practitioners. Focuses on booking consultations.",
      features: ["Specialty Selection", "Emergency Contact Block", "Clinic Hours Widget", "Book Visit Form"],
      icon: "🏥",
      image: "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?q=80&w=600"
    },
    {
      id: "School",
      title: "Pre-School & Academy Portal",
      desc: "Cozy educational styling. Includes academic curriculum grids, admission brochure inquiries, and virtual campus logs.",
      features: ["Grade Syllabus Guides", "Enrollment Brochures", "Parent Inquiry Forms", "Virtual Tour Highlights"],
      icon: "🏫",
      image: "https://images.unsplash.com/photo-1580582932707-520aed937b7b?q=80&w=600"
    },
    {
      id: "Real Estate",
      title: "Luxury Estates Brokerage Portal",
      desc: "Premium real estate agency layouts. Features property search lists, budget selections, and consultant booking.",
      features: ["Property Filtering Grid", "Commercial & Home Categories", "Budget Matchers", "Consultant Request Form"],
      icon: "🏢",
      image: "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?q=80&w=600"
    }
  ]

  useEffect(() => {
    fetch(`${API_BASE}/leads/?limit=100`)
      .then(res => res.json())
      .then(data => {
        setLeads(data.leads || [])
        if (data.leads && data.leads.length > 0) {
          setSelectedLeadId(data.leads[0].id)
        }
      })
      .catch(err => console.error("Error loading leads for portfolio dropdown:", err))
  }, [])

  const generatePrototype = (nicheId) => {
    if (!selectedLeadId) {
      triggerAlert("Please select a lead first", "error")
      return
    }

    const payload = {
      lead_id: parseInt(selectedLeadId),
      niche: nicheId
    }

    fetch(`${API_BASE}/portfolio/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          triggerAlert(`Interactive ${nicheId} demo generated!`)
          setActivePrototypes({
            ...activePrototypes,
            [nicheId]: `${API_BASE.replace(/\/api\/?$/, '')}${data.preview_url}`
          })
        }
      })
      .catch(err => {
        console.error("Error generating portfolio prototype:", err)
        triggerAlert("Error generating prototype website", "error")
      })
  }

  const copyLink = (nicheId) => {
    const url = activePrototypes[nicheId]
    if (url) {
      navigator.clipboard.writeText(url)
      triggerAlert("Prototype link copied to clipboard!")
    }
  }

  return (
    <div className="space-y-6">
      
      {/* Top selection card */}
      <div className="p-4 sm:p-6 rounded-2xl bg-zinc-900/50 backdrop-blur-md border border-zinc-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide uppercase">Interactive Portfolio Builder</h3>
          <p className="text-xs text-zinc-500 mt-1">Generate live customized landing pages loaded with the selected lead's company info, phone, and location.</p>
        </div>
        
        {/* Dropdown selectors */}
        <div className="w-full md:w-80 shrink-0 text-xs">
          <label className="block text-zinc-500 font-bold mb-1">Select Customizing Lead</label>
          <select
            value={selectedLeadId}
            onChange={(e) => {
              setSelectedLeadId(e.target.value)
              setActivePrototypes({}) // reset generated links for safety
            }}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-white focus:outline-none"
          >
            <option value="" disabled>Choose Lead...</option>
            {leads.map(l => (
              <option key={l.id} value={l.id}>{l.business_name} ({l.city})</option>
            ))}
          </select>
        </div>
      </div>

      {/* Grid of niche cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {niches.map(niche => {
          const generatedUrl = activePrototypes[niche.id]
          return (
            <div key={niche.id} className="rounded-2xl border border-zinc-800 bg-zinc-900/30 overflow-hidden flex flex-col justify-between">
              
              <div>
                {/* Image card preview header */}
                <div className="relative h-36 sm:h-40 bg-zinc-950 overflow-hidden">
                  <img src={niche.image} alt={niche.title} className="w-full h-full object-cover opacity-60 hover:scale-105 transition duration-500" />
                  <span className="absolute top-3 left-3 bg-zinc-950/80 border border-zinc-850 px-2 py-1 rounded text-lg">{niche.icon}</span>
                  <span className="absolute bottom-3 right-3 text-[10px] bg-indigo-900/60 border border-indigo-800 text-indigo-300 font-extrabold uppercase px-2 py-0.5 rounded tracking-wide">
                    {niche.id} template
                  </span>
                </div>

                {/* Content description */}
                <div className="p-4 sm:p-5 space-y-4">
                  <div>
                    <h4 className="text-sm font-bold text-white leading-snug">{niche.title}</h4>
                    <p className="text-[11px] text-zinc-500 mt-1 leading-relaxed">{niche.desc}</p>
                  </div>

                  {/* Bullet points */}
                  <div className="space-y-1">
                    <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider block">Features included</span>
                    <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[10px] text-zinc-500">
                      {niche.features.map(f => (
                        <li key={f} className="flex items-center gap-1">
                          <span className="text-indigo-400">&bull;</span>
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Actions footer */}
              <div className="p-4 sm:p-5 border-t border-zinc-800/40 bg-zinc-950/20 text-xs space-y-3">
                {generatedUrl ? (
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <a
                        href={generatedUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-center flex items-center justify-center gap-1.5 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Launch Live Site</span>
                      </a>
                      <button
                        onClick={() => copyLink(niche.id)}
                        className="px-3 bg-zinc-900 hover:bg-zinc-850 border border-zinc-800 text-zinc-400 hover:text-white rounded-lg flex items-center justify-center transition"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <span className="text-[9px] text-zinc-500 font-mono block text-center truncate">Preview: {generatedUrl}</span>
                  </div>
                ) : (
                  <button
                    onClick={() => generatePrototype(niche.id)}
                    className="w-full py-2.5 bg-zinc-900 hover:bg-zinc-850 border border-zinc-800 text-white font-bold rounded-lg flex items-center justify-center gap-1.5 transition"
                  >
                    <LayoutTemplate className="w-3.5 h-3.5" />
                    <span>Customize Demo Portfolio</span>
                  </button>
                )}
              </div>

            </div>
          )
        })}
      </div>

    </div>
  )
}
