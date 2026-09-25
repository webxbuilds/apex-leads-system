import os
import time
import logging
from sqlalchemy.orm import Session
from backend.app.db.models import Lead, Proposal, AnalysisReport

logger = logging.getLogger(__name__)

PROPOSALS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "proposals"))
os.makedirs(PROPOSALS_DIR, exist_ok=True)

def create_proposal_document(lead_id: int, doc_type: str, title: str, items: list, db: Session) -> Proposal:
    """
    Module 6: Proposal Generator
    Generates Quotations, Invoices, Proposals, and Contracts in beautifully styled, printable HTML documents.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead with ID {lead_id} not found.")

    report = db.query(AnalysisReport).filter(AnalysisReport.lead_id == lead_id).order_by(AnalysisReport.created_at.desc()).first()

    # Define default line items if empty
    if not items:
        items = _get_default_items_for_gaps(report)

    # Subtotal calculation
    subtotal = sum(item.get("price", 0) for item in items)
    tax = round(subtotal * 0.18, 2)  # 18% GST/tax
    total = round(subtotal + tax, 2)

    doc_filename = f"{doc_type.lower()}_lead_{lead_id}_{int(time.time())}.html"
    file_path = os.path.join(PROPOSALS_DIR, doc_filename)

    # Build the document based on type
    if doc_type.upper() == "PROPOSAL":
        content = _build_proposal_html(lead, title, items, subtotal, tax, total)
    elif doc_type.upper() == "QUOTATION":
        content = _build_quotation_html(lead, title, items, subtotal, tax, total)
    elif doc_type.upper() == "INVOICE":
        content = _build_invoice_html(lead, title, items, subtotal, tax, total)
    elif doc_type.upper() == "CONTRACT":
        content = _build_contract_html(lead, title, items, subtotal, tax, total)
    else:
        raise ValueError(f"Unsupported document type: {doc_type}")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    proposal = Proposal(
        lead_id=lead_id,
        proposal_type=doc_type,
        title=title,
        status="Draft",
        file_path=f"/static/proposals/{doc_filename}"
    )

    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    return proposal


def _get_default_items_for_gaps(report: AnalysisReport) -> list:
    items = []
    
    # Check what gaps exist and charge for them
    if report:
        if not report.is_mobile_responsive:
            items.append({
                "description": "Mobile-Responsive Layout Redesign",
                "details": "Restructuring the page layout using flexible CSS grids to display beautifully across smartphones and tablets.",
                "price": 12000
            })
        if not report.has_https:
            items.append({
                "description": "SSL Certificate & Security Protocol Setup",
                "details": "Procuring, installing, and configuring Let's Encrypt SSL. Redirecting HTTP traffic to secure HTTPS.",
                "price": 3000
            })
        if report.load_speed_seconds > 2.5:
            items.append({
                "description": "Page Speed & Performance Optimization",
                "details": "Optimizing visual assets, deferring render-blocking scripts, and configuring cache engines.",
                "price": 6000
            })
        if not report.has_contact_form:
            items.append({
                "description": "Lead Capture Form & Autoresponder Integration",
                "details": "Adding optimized lead generation forms synced with email response integrations.",
                "price": 4000
            })
        if not report.has_whatsapp_button:
            items.append({
                "description": "WhatsApp Floating Chat Integration",
                "details": "Adding direct contact messaging channels on the front-end homepage.",
                "price": 2000
            })
            
    # Fallback to general redesign package if minimal gaps
    if not items:
        items.append({
            "description": "Premium Website UI/UX Redesign Package",
            "details": "Complete homepage & subpages overhaul. Modern typography, fast loading, custom assets.",
            "price": 25000
        })
        items.append({
            "description": "Local SEO & Google Business Optimization",
            "details": "Structured meta tags, alt tags fixes, and ranking configuration.",
            "price": 8000
        })

    return items


def _get_header_html(doc_type: str, title: str, doc_number: str) -> str:
    return f"""
    <div class="flex justify-between items-start border-b border-zinc-800 pb-8 mb-8">
        <div>
            <div class="flex items-center gap-2 mb-4">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-fuchsia-500 flex items-center justify-center font-bold text-white text-lg">💡</div>
                <span class="font-bold text-white text-lg tracking-tight">ApexWeb Agency</span>
            </div>
            <p class="text-xs text-zinc-500">102, Innovation Hub, Sector 62, Noida, UP, India</p>
            <p class="text-xs text-zinc-500">billing@apexweb.agency | +91 98765 43210</p>
        </div>
        <div class="text-right">
            <h1 class="text-2xl font-extrabold text-white uppercase tracking-wider">{doc_type}</h1>
            <p class="text-xs text-zinc-400 mt-1">{title}</p>
            <p class="text-xs text-indigo-400 font-bold mt-2">{doc_number}</p>
            <p class="text-xs text-zinc-500 mt-1">Date: {time.strftime("%d %b, %Y")}</p>
        </div>
    </div>
    """


def _get_doc_scaffolding(doc_type: str, main_content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ApexWeb Agency - {doc_type}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
        body {{
            font-family: 'Outfit', sans-serif;
            background-color: #09090b;
        }}
        @media print {{
            body {{
                background-color: #ffffff;
                color: #000000;
            }}
            .no-print {{
                display: none;
            }}
            .print-border {{
                border-color: #e4e4e7 !important;
            }}
            .print-text-dark {{
                color: #09090b !important;
            }}
            .print-text-muted {{
                color: #71717a !important;
            }}
            .print-bg-light {{
                background-color: #f4f4f5 !important;
            }}
        }}
    </style>
</head>
<body class="text-zinc-300 min-h-screen py-12 px-6">
    <div class="no-print max-w-4xl mx-auto mb-6 flex justify-between items-center">
        <a href="javascript:window.history.back();" class="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-xs hover:bg-zinc-800 transition">&larr; Back to Dashboard</a>
        <button onclick="window.print();" class="px-5 py-2 bg-indigo-500 text-white font-bold text-xs rounded-xl hover:bg-indigo-600 transition flex items-center gap-2">🖨️ Print / Save as PDF</button>
    </div>

    <div class="max-w-4xl mx-auto bg-zinc-950 border border-zinc-800 rounded-3xl p-10 print-border shadow-2xl">
        {main_content}
    </div>
</body>
</html>
"""


def _build_proposal_html(lead: Lead, title: str, items: list, subtotal: float, tax: float, total: float) -> str:
    # Build list elements
    items_html = ""
    for idx, item in enumerate(items, 1):
        items_html += f"""
        <div class="mb-6 p-5 bg-zinc-900 border border-zinc-800 rounded-xl">
            <h4 class="text-white font-semibold text-sm mb-1">{idx}. {item['description']}</h4>
            <p class="text-zinc-400 text-xs">{item['details']}</p>
        </div>
        """

    content = f"""
    {_get_header_html("Project Proposal", title, f"PROP-2026-{lead.id}")}
    
    <div class="mb-8">
        <h2 class="text-zinc-400 text-xs uppercase font-bold tracking-wider mb-2">Prepared For</h2>
        <h3 class="text-white text-lg font-bold">{lead.business_name}</h3>
        <p class="text-xs text-zinc-500">Contact: {lead.owner_name or 'Business Owner'} | Location: {lead.city}</p>
        <p class="text-xs text-zinc-500">Website: {lead.website or 'None'}</p>
    </div>

    <div class="mb-8 border-t border-zinc-800 pt-6">
        <h2 class="text-white text-base font-bold mb-3">1. Executive Summary</h2>
        <p class="text-zinc-400 text-xs leading-relaxed">
            ApexWeb Agency is pleased to submit this proposal to rebuild, optimize, and launch a conversion-focused web portal for {lead.business_name}. 
            Our digital audit identified essential parameters affecting your site performance. Correcting these will secure your web visibility, lower bounce rates, and automate booking acquisition.
        </p>
    </div>

    <div class="mb-8">
        <h2 class="text-white text-base font-bold mb-4">2. Scope of Work</h2>
        {items_html}
    </div>

    <div class="mb-8 border-t border-zinc-800 pt-6">
        <h2 class="text-white text-base font-bold mb-2">3. Investment & Deliverables</h2>
        <p class="text-zinc-400 text-xs mb-4">The comprehensive budget for the execution of the scoped items is itemized below:</p>
        
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <div class="flex justify-between text-xs text-zinc-400 pb-2 border-b border-zinc-800">
                <span>Core Services</span>
                <span>INR {subtotal:,.2f}</span>
            </div>
            <div class="flex justify-between text-xs text-zinc-400 py-2 border-b border-zinc-800">
                <span>Tax (18% GST)</span>
                <span>INR {tax:,.2f}</span>
            </div>
            <div class="flex justify-between text-sm font-bold text-white pt-3">
                <span>Total Project Investment</span>
                <span class="text-indigo-400">INR {total:,.2f}</span>
            </div>
        </div>
    </div>

    <div class="border-t border-zinc-800 pt-8 mt-12 grid grid-cols-2 gap-8 text-center">
        <div>
            <div class="h-16 border-b border-zinc-800 flex items-end justify-center pb-2 text-zinc-600 text-xs">Signature / Date</div>
            <p class="text-xs text-zinc-500 mt-2 font-bold uppercase">ApexWeb Agency Representative</p>
        </div>
        <div>
            <div class="h-16 border-b border-zinc-800 flex items-end justify-center pb-2 text-zinc-600 text-xs">Signature / Date</div>
            <p class="text-xs text-zinc-500 mt-2 font-bold uppercase">{lead.business_name} Representative</p>
        </div>
    </div>
    """
    return _get_doc_scaffolding("Project Proposal", content)


def _build_quotation_html(lead: Lead, title: str, items: list, subtotal: float, tax: float, total: float) -> str:
    rows = ""
    for idx, item in enumerate(items, 1):
        rows += f"""
        <tr class="border-b border-zinc-800 text-xs">
            <td class="py-4 text-white font-medium">{idx}</td>
            <td class="py-4">
                <span class="text-white block font-semibold">{item['description']}</span>
                <span class="text-zinc-500 block text-[10px] mt-0.5">{item['details']}</span>
            </td>
            <td class="py-4 text-right">INR {item['price']:,.2f}</td>
        </tr>
        """
        
    content = f"""
    {_get_header_html("Quotation", title, f"QUOT-2026-{lead.id}")}
    
    <div class="mb-8">
        <h2 class="text-zinc-400 text-xs uppercase font-bold tracking-wider mb-2">Quote Prepared For</h2>
        <h3 class="text-white text-lg font-bold">{lead.business_name}</h3>
        <p class="text-xs text-zinc-500">Contact: {lead.owner_name or 'Business Owner'} | Location: {lead.city}</p>
    </div>

    <table class="w-full text-left mb-8">
        <thead>
            <tr class="border-b border-zinc-800 text-zinc-500 text-xs uppercase font-bold">
                <th class="pb-3 w-10">#</th>
                <th class="pb-3">Description / Details</th>
                <th class="pb-3 text-right">Amount</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>

    <div class="flex justify-end">
        <div class="w-80 bg-zinc-900 border border-zinc-800 rounded-2xl p-5 text-xs text-zinc-400 space-y-2">
            <div class="flex justify-between">
                <span>Subtotal</span>
                <span class="text-white font-medium">INR {subtotal:,.2f}</span>
            </div>
            <div class="flex justify-between">
                <span>GST (18%)</span>
                <span class="text-white font-medium">INR {tax:,.2f}</span>
            </div>
            <div class="flex justify-between text-sm font-bold text-white pt-2 border-t border-zinc-800">
                <span>Quote Total</span>
                <span class="text-indigo-400">INR {total:,.2f}</span>
            </div>
        </div>
    </div>

    <div class="mt-12 text-[10px] text-zinc-500 border-t border-zinc-800 pt-6">
        <p class="font-semibold uppercase mb-1">Terms & Conditions</p>
        <p>1. This quotation is valid for 30 days from the date of issue.</p>
        <p>2. Payments: 50% advance to start work, 50% post completion and approval.</p>
        <p>3. Timeline: Deliverable schedules will launch immediately upon receiving credentials.</p>
    </div>
    """
    return _get_doc_scaffolding("Quotation", content)


def _build_invoice_html(lead: Lead, title: str, items: list, subtotal: float, tax: float, total: float) -> str:
    rows = ""
    for idx, item in enumerate(items, 1):
        rows += f"""
        <tr class="border-b border-zinc-800 text-xs">
            <td class="py-4 text-white font-medium">{idx}</td>
            <td class="py-4">
                <span class="text-white block font-semibold">{item['description']}</span>
            </td>
            <td class="py-4 text-right">INR {item['price']:,.2f}</td>
        </tr>
        """

    content = f"""
    {_get_header_html("Invoice", title, f"INV-2026-{lead.id}")}
    
    <div class="grid grid-cols-2 gap-8 mb-8 text-xs">
        <div>
            <h2 class="text-zinc-500 font-bold uppercase tracking-wider mb-2">Billed To</h2>
            <h3 class="text-white text-sm font-bold">{lead.business_name}</h3>
            <p class="text-zinc-400 mt-1">{lead.owner_name or 'Business Owner'}</p>
            <p class="text-zinc-400">{lead.city}</p>
        </div>
        <div class="text-right">
            <h2 class="text-zinc-500 font-bold uppercase tracking-wider mb-2">Status</h2>
            <span class="inline-block px-3 py-1 bg-amber-950 text-amber-400 border border-amber-800 rounded-full font-bold text-[10px]">PAYMENT DUE</span>
            <p class="text-zinc-500 mt-3">Due Date: Within 7 days of approval</p>
        </div>
    </div>

    <table class="w-full text-left mb-8">
        <thead>
            <tr class="border-b border-zinc-800 text-zinc-500 text-xs uppercase font-bold">
                <th class="pb-3 w-10">#</th>
                <th class="pb-3">Line Item</th>
                <th class="pb-3 text-right">Amount</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>

    <div class="flex justify-between items-start mt-8">
        <div class="text-xs text-zinc-500">
            <p class="font-bold uppercase text-white mb-2">Bank Transfer Details</p>
            <p>Bank: HDFC Bank Ltd</p>
            <p>A/C Name: ApexWeb Agency Private Limited</p>
            <p>A/C No: 50200084739103</p>
            <p>IFSC Code: HDFC0000120</p>
        </div>
        <div class="w-80 bg-zinc-900 border border-zinc-800 rounded-2xl p-5 text-xs text-zinc-400 space-y-2">
            <div class="flex justify-between">
                <span>Subtotal</span>
                <span class="text-white font-medium">INR {subtotal:,.2f}</span>
            </div>
            <div class="flex justify-between">
                <span>GST (18%)</span>
                <span class="text-white font-medium">INR {tax:,.2f}</span>
            </div>
            <div class="flex justify-between text-sm font-bold text-white pt-2 border-t border-zinc-800">
                <span>Total Due</span>
                <span class="text-indigo-400">INR {total:,.2f}</span>
            </div>
        </div>
    </div>
    """
    return _get_doc_scaffolding("Invoice", content)


def _build_contract_html(lead: Lead, title: str, items: list, subtotal: float, tax: float, total: float) -> str:
    content = f"""
    {_get_header_html("Service Agreement", title, f"SLA-2026-{lead.id}")}
    
    <div class="mb-8">
        <h2 class="text-zinc-500 text-xs uppercase font-bold tracking-wider mb-2">Parties Involved</h2>
        <p class="text-xs text-zinc-400 leading-relaxed">
            This Service Agreement (the "Agreement") is entered into and made effective as of {time.strftime("%B %d, %Y")}, by and between 
            <strong>ApexWeb Agency</strong> ("Service Provider"), and <strong>{lead.business_name}</strong> ("Client"), located in {lead.city}.
        </p>
    </div>

    <div class="space-y-6 text-xs text-zinc-400 leading-relaxed">
        <div>
            <h3 class="text-white font-bold text-sm mb-1">1. Retainer & Scope of Services</h3>
            <p>
                Service Provider agrees to deploy standard optimizations detailed in Project Proposal PROP-2026-{lead.id}. 
                Specifically: Website redesign, deployment of security features, performance engineering, and conversion forms setup.
            </p>
        </div>
        <div>
            <h3 class="text-white font-bold text-sm mb-1">2. Payment Terms</h3>
            <p>
                Client agrees to pay Service Provider a total consideration of <strong>INR {total:,.2f}</strong> (inclusive of GST taxes). 
                An initial mobilization fee of 50% (INR {total*0.5:,.2f}) is due upon signing. The final 50% is due immediately upon staging deployment and completion check.
            </p>
        </div>
        <div>
            <h3 class="text-white font-bold text-sm mb-1">3. Timelines & Performance</h3>
            <p>
                Deliverables will be completed within 14 calendar days from the receipt of required assets (domain access, business imagery, specific copy details).
            </p>
        </div>
        <div>
            <h3 class="text-white font-bold text-sm mb-1">4. Confidentiality & Intellectual Property</h3>
            <p>
                All source code, UI designs, and marketing assets developed for the client will belong exclusively to the Client upon receipt of final settlement.
            </p>
        </div>
    </div>

    <div class="border-t border-zinc-800 pt-8 mt-12 grid grid-cols-2 gap-8 text-center">
        <div>
            <div class="h-16 border-b border-zinc-800 flex items-end justify-center pb-2 text-zinc-600 text-xs">Signature / Date</div>
            <p class="text-xs text-zinc-500 mt-2 font-bold uppercase">Authorized Representative<br>ApexWeb Agency</p>
        </div>
        <div>
            <div class="h-16 border-b border-zinc-800 flex items-end justify-center pb-2 text-zinc-600 text-xs">Signature / Date</div>
            <p class="text-xs text-zinc-500 mt-2 font-bold uppercase">Authorized Representative<br>{lead.business_name}</p>
        </div>
    </div>
    """
    return _get_doc_scaffolding("Service Agreement", content)
