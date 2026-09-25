import logging
from sqlalchemy.orm import Session
from backend.app.db.models import Lead, PortfolioDemo

logger = logging.getLogger(__name__)

def generate_demo_portfolio(lead_id: int, niche: str, db: Session) -> str:
    """
    Module 10: Portfolio Generator
    Generates or fetches a customized, beautiful prototype link for a lead based on their industry niche.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead with ID {lead_id} not found.")

    business_name = lead.business_name
    category = niche or lead.category or "Business"

    # Search if database has record
    demo = db.query(PortfolioDemo).filter(
        PortfolioDemo.lead_id == lead_id,
        PortfolioDemo.niche == category
    ).first()

    demo_url = f"/api/portfolio/preview/{lead_id}?niche={category}"

    if not demo:
        demo = PortfolioDemo(
            lead_id=lead_id,
            niche=category,
            business_name=business_name,
            demo_url=demo_url
        )
        db.add(demo)
        db.commit()
        db.refresh(demo)

    return demo_url


def render_portfolio_html(lead: Lead, niche: str) -> str:
    """
    Renders custom single-page demo websites with rich layouts,
    specific styling, pricing tables, hero sections, and active lead forms.
    """
    business_name = lead.business_name
    phone = lead.phone or "+91 98765 43210"
    email = lead.email or f"hello@{business_name.lower().replace(' ', '')}.com"
    address = lead.address or f"Main Ring Road, {lead.city}"
    city = lead.city or "City"

    # Niche-specific template builder
    if niche.lower() == "restaurant":
        return _get_restaurant_template(business_name, phone, email, address, city)
    elif niche.lower() == "gym":
        return _get_gym_template(business_name, phone, email, address, city)
    elif niche.lower() == "salon":
        return _get_salon_template(business_name, phone, email, address, city)
    elif niche.lower() == "dentist":
        return _get_dentist_template(business_name, phone, email, address, city)
    elif niche.lower() == "clinic":
        return _get_clinic_template(business_name, phone, email, address, city)
    elif niche.lower() == "school":
        return _get_school_template(business_name, phone, email, address, city)
    elif niche.lower() == "real estate":
        return _get_realestate_template(business_name, phone, email, address, city)
    elif niche.lower() == "hospital":
        return _get_hospital_template(business_name, phone, email, address, city)
    elif niche.lower() == "lawyer":
        return _get_lawyer_template(business_name, phone, email, address, city)
    elif niche.lower() == "ecommerce":
        return _get_ecommerce_template(business_name, phone, email, address, city)
    else:
        # Generic corporate fallback
        return _get_corporate_template(business_name, phone, email, address, city)


def _get_base_head(business_name: str, font_name: str = "Outfit") -> str:
    return f"""
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - Premium Showcase</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family={font_name}:wght@300;400;500;600;700;800&display=swap');
        body {{
            font-family: '{font_name}', sans-serif;
        }}
    </style>
    """


def _get_restaurant_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    {_get_base_head(name, "Outfit")}
</head>
<body class="bg-stone-950 text-stone-200">
    <header class="border-b border-stone-800 bg-stone-950/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <span class="font-bold text-white text-xl tracking-wider">🍴 {name}</span>
            <nav class="hidden md:flex gap-6 text-sm text-stone-400">
                <a href="#menu" class="hover:text-amber-500 transition">Menu</a>
                <a href="#about" class="hover:text-amber-500 transition">About</a>
                <a href="#reserve" class="hover:text-amber-500 transition">Reservations</a>
            </nav>
            <a href="#reserve" class="px-5 py-2 bg-amber-500 text-stone-950 font-bold text-xs rounded-full hover:bg-amber-600 transition">Book Table</a>
        </div>
    </header>

    <!-- Hero -->
    <section class="relative bg-stone-900 py-32 text-center overflow-hidden">
        <div class="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=1200')] bg-cover bg-center opacity-25"></div>
        <div class="relative max-w-4xl mx-auto px-6">
            <span class="text-amber-500 text-xs font-bold uppercase tracking-widest">Experience Local Fine Dining</span>
            <h1 class="text-4xl md:text-6xl font-black text-white mt-4 tracking-tight leading-tight">{name}</h1>
            <p class="text-stone-300 mt-4 text-base md:text-lg max-w-2xl mx-auto">Savor exquisite culinary art crafted from seasonal local ingredients. Reserve your exclusive culinary journey in {city} today.</p>
            <div class="mt-8 flex justify-center gap-4">
                <a href="#reserve" class="px-6 py-3 bg-amber-500 text-stone-950 font-extrabold text-sm rounded-xl hover:bg-amber-600 transition">Book Table</a>
                <a href="#menu" class="px-6 py-3 bg-stone-800 text-white font-bold text-sm rounded-xl hover:bg-stone-700 transition">Explore Menu</a>
            </div>
        </div>
    </section>

    <!-- Menu -->
    <section id="menu" class="max-w-6xl mx-auto px-6 py-20">
        <div class="text-center mb-12">
            <h2 class="text-3xl font-bold text-white">Chef's Signature Selections</h2>
            <p class="text-stone-400 text-sm mt-2">Curated recipes representing modern gastronomical design</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div class="flex justify-between border-b border-stone-800 pb-4">
                <div>
                    <h3 class="font-bold text-white">Hand-Crafted Filet Mignon</h3>
                    <p class="text-xs text-stone-500 mt-1">Aged beef tenderloin, truffle potato puree, organic seasonal greens</p>
                </div>
                <span class="font-bold text-amber-500">INR 1,290</span>
            </div>
            <div class="flex justify-between border-b border-stone-800 pb-4">
                <div>
                    <h3 class="font-bold text-white">Wild Salmon Risotto</h3>
                    <p class="text-xs text-stone-500 mt-1">Pan-seared Atlantic salmon, saffron risotto, preserved lemon oils</p>
                </div>
                <span class="font-bold text-amber-500">INR 980</span>
            </div>
            <div class="flex justify-between border-b border-stone-800 pb-4">
                <div>
                    <h3 class="font-bold text-white">Pan-Seared Organic Gnocchi</h3>
                    <p class="text-xs text-stone-500 mt-1">Handmade potato dumplings, wild forest mushrooms, sage butter emulsion</p>
                </div>
                <span class="font-bold text-amber-500">INR 750</span>
            </div>
            <div class="flex justify-between border-b border-stone-800 pb-4">
                <div>
                    <h3 class="font-bold text-white">Decadent Pistachio Soufflé</h3>
                    <p class="text-xs text-stone-500 mt-1">Warm pistachio lava filling, cardamom bean ice cream scoop</p>
                </div>
                <span class="font-bold text-amber-500">INR 450</span>
            </div>
        </div>
    </section>

    <!-- Reservations Form -->
    <section id="reserve" class="bg-stone-900/50 py-20 border-t border-stone-800">
        <div class="max-w-md mx-auto px-6 bg-stone-950 border border-stone-800 rounded-3xl p-8 shadow-2xl">
            <h2 class="text-2xl font-bold text-white text-center mb-6">Reserve Table</h2>
            <form onsubmit="event.preventDefault(); alert('Reservation submitted successfully!');" class="space-y-4 text-sm">
                <div>
                    <label class="block text-stone-400 mb-1">Full Name</label>
                    <input type="text" required class="w-full bg-stone-900 border border-stone-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-amber-500">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-stone-400 mb-1">Date</label>
                        <input type="date" required class="w-full bg-stone-900 border border-stone-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-amber-500">
                    </div>
                    <div>
                        <label class="block text-stone-400 mb-1">Time</label>
                        <input type="time" required class="w-full bg-stone-900 border border-stone-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-amber-500">
                    </div>
                </div>
                <div>
                    <label class="block text-stone-400 mb-1">Guests</label>
                    <select class="w-full bg-stone-900 border border-stone-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-amber-500">
                        <option>2 People</option>
                        <option>4 People</option>
                        <option>6 People</option>
                        <option>8+ People</option>
                    </select>
                </div>
                <button type="submit" class="w-full py-3 bg-amber-500 text-stone-950 font-bold rounded-xl hover:bg-amber-600 transition">Confirm Booking</button>
            </form>
        </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-stone-800 py-12 text-center text-xs text-stone-500">
        <p class="text-stone-400 font-bold mb-2">{name}</p>
        <p>Location: {addr} | Phone: {phone} | Email: {email}</p>
        <p class="mt-4">&copy; 2026 {name}. All Rights Reserved.</p>
    </footer>
</body>
</html>
"""


def _get_gym_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    {_get_base_head(name, "Outfit")}
</head>
<body class="bg-zinc-950 text-zinc-200">
    <header class="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <span class="font-extrabold text-white text-xl tracking-tight">🏋️ {name.upper()}</span>
            <a href="#join" class="px-5 py-2 bg-red-600 text-white font-bold text-xs rounded-lg hover:bg-red-700 transition uppercase tracking-wider">Free Trial Pass</a>
        </div>
    </header>

    <!-- Hero -->
    <section class="relative bg-zinc-900 py-32 text-center overflow-hidden">
        <div class="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=1200')] bg-cover bg-center opacity-20"></div>
        <div class="relative max-w-4xl mx-auto px-6">
            <span class="text-red-500 text-xs font-bold uppercase tracking-wider bg-red-950/50 border border-red-900 px-3 py-1 rounded">No Excuses. Only Results.</span>
            <h1 class="text-4xl md:text-6xl font-black text-white mt-6 uppercase tracking-tight">{name}</h1>
            <p class="text-zinc-300 mt-4 text-base md:text-lg max-w-2xl mx-auto">Unleash your strength. Apex equipment, professional coaching, and a driven community waiting to push you past boundaries in {city}.</p>
            <div class="mt-8">
                <a href="#join" class="px-8 py-4 bg-red-600 text-white font-bold text-sm rounded-lg hover:bg-red-700 transition uppercase tracking-wider">Claim Free Pass</a>
            </div>
        </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="max-w-6xl mx-auto px-6 py-20">
        <h2 class="text-3xl font-black text-white text-center mb-12 uppercase tracking-wide">Choose Your Plan</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div class="p-6 bg-zinc-900 border border-zinc-800 rounded-2xl">
                <span class="text-xs text-zinc-500 font-bold uppercase">Basic</span>
                <div class="text-3xl font-bold text-white mt-2">INR 1,500<span class="text-xs font-normal text-zinc-500">/mo</span></div>
                <ul class="mt-6 space-y-3 text-xs text-zinc-400">
                    <li>Access to Cardio & Weight area</li>
                    <li>Locker room access</li>
                    <li>1 Free Fitness Assessment</li>
                </ul>
            </div>
            <div class="p-6 bg-zinc-900 border-2 border-red-600 rounded-2xl relative">
                <span class="absolute -top-3 right-6 bg-red-600 text-white text-[10px] px-2 py-0.5 rounded font-bold uppercase">Popular</span>
                <span class="text-xs text-zinc-400 font-bold uppercase">Gold Retainer</span>
                <div class="text-3xl font-bold text-white mt-2">INR 2,800<span class="text-xs font-normal text-zinc-500">/mo</span></div>
                <ul class="mt-6 space-y-3 text-xs text-zinc-400">
                    <li>24/7 Access to Gym floor</li>
                    <li>Unlimited Group Classes (Yoga, MMA)</li>
                    <li>3 Personal Training Sessions</li>
                    <li>Diet Plan Chart customization</li>
                </ul>
            </div>
            <div class="p-6 bg-zinc-900 border border-zinc-800 rounded-2xl">
                <span class="text-xs text-zinc-500 font-bold uppercase">Platinum Elite</span>
                <div class="text-3xl font-bold text-white mt-2">INR 5,000<span class="text-xs font-normal text-zinc-500">/mo</span></div>
                <ul class="mt-6 space-y-3 text-xs text-zinc-400">
                    <li>All Gym Facilities + Spa Access</li>
                    <li>1-on-1 Dedicated Coach</li>
                    <li>Weekly Body Composition Auditing</li>
                    <li>VIP towel and shake service</li>
                </ul>
            </div>
        </div>
    </section>

    <!-- Join form -->
    <section id="join" class="bg-zinc-900 border-t border-zinc-800 py-20">
        <div class="max-w-md mx-auto px-6 bg-zinc-950 border border-zinc-800 rounded-2xl p-8">
            <h2 class="text-2xl font-bold text-white text-center uppercase mb-6">Get Guest Pass</h2>
            <form onsubmit="event.preventDefault(); alert('Trial voucher sent to your phone!');" class="space-y-4 text-xs">
                <div>
                    <label class="block text-zinc-400 mb-1">Full Name</label>
                    <input type="text" required class="w-full bg-zinc-900 border border-zinc-800 rounded p-2.5 text-white">
                </div>
                <div>
                    <label class="block text-zinc-400 mb-1">Phone Number</label>
                    <input type="tel" required class="w-full bg-zinc-900 border border-zinc-800 rounded p-2.5 text-white">
                </div>
                <button type="submit" class="w-full py-3 bg-red-600 text-white font-bold rounded hover:bg-red-700 transition uppercase tracking-wider">Send Pass Details</button>
            </form>
        </div>
    </section>

    <footer class="py-12 border-t border-zinc-800 text-center text-xs text-zinc-500">
        <p class="text-white font-bold mb-2">{name}</p>
        <p>{addr} | {phone} | {email}</p>
        <p class="mt-4">&copy; 2026 {name}. Get Strong.</p>
    </footer>
</body>
</html>
"""


def _get_salon_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    {_get_base_head(name, "Outfit")}
</head>
<body class="bg-zinc-950 text-zinc-300">
    <header class="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <span class="font-extrabold text-white text-xl tracking-wide">✂️ {name}</span>
            <a href="#book" class="px-5 py-2.5 bg-fuchsia-600 text-white font-bold text-xs rounded-full hover:bg-fuchsia-700 transition">Book Appointment</a>
        </div>
    </header>

    <!-- Hero -->
    <section class="relative bg-zinc-900 py-32 text-center overflow-hidden">
        <div class="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1560066984-138dadb4c035?q=80&w=1200')] bg-cover bg-center opacity-25"></div>
        <div class="relative max-w-4xl mx-auto px-6">
            <span class="text-fuchsia-400 text-xs font-bold uppercase tracking-widest">Premium Hair & Beauty Care</span>
            <h1 class="text-4xl md:text-6xl font-black text-white mt-6 tracking-tight">{name}</h1>
            <p class="text-zinc-300 mt-4 text-base max-w-xl mx-auto">Reinvent your look. Professional styling, color extensions, and skin rejuvenation services in {city}.</p>
            <div class="mt-8">
                <a href="#book" class="px-8 py-3 bg-fuchsia-600 text-white font-bold text-sm rounded-full hover:bg-fuchsia-700 transition">Book Appointment</a>
            </div>
        </div>
    </section>

    <!-- Services -->
    <section class="max-w-5xl mx-auto px-6 py-20">
        <h2 class="text-2xl font-bold text-white text-center mb-12">Our Signature Stylings</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm">
            <div class="flex justify-between border-b border-zinc-800 pb-3">
                <div>
                    <span class="text-white font-semibold">Premium Haircut & Blow Dry</span>
                    <span class="block text-xs text-zinc-500 mt-1">Includes custom wash, conditioning, and thermal finish.</span>
                </div>
                <span class="font-bold text-fuchsia-400">INR 1,200</span>
            </div>
            <div class="flex justify-between border-b border-zinc-800 pb-3">
                <div>
                    <span class="text-white font-semibold">Balayage & Color Correction</span>
                    <span class="block text-xs text-zinc-500 mt-1">Hand-painted custom highlighting tailored to hair flow.</span>
                </div>
                <span class="font-bold text-fuchsia-400">INR 4,500</span>
            </div>
            <div class="flex justify-between border-b border-zinc-800 pb-3">
                <div>
                    <span class="text-white font-semibold">Hydrafacial Rejuvenation</span>
                    <span class="block text-xs text-zinc-500 mt-1">Cleanses, exfoliates, and nourishes the skin.</span>
                </div>
                <span class="font-bold text-fuchsia-400">INR 2,800</span>
            </div>
            <div class="flex justify-between border-b border-zinc-800 pb-3">
                <div>
                    <span class="text-white font-semibold">Bridal Glow Makeover Package</span>
                    <span class="block text-xs text-zinc-500 mt-1">Hair styling, HD makeup, draping, and setting.</span>
                </div>
                <span class="font-bold text-fuchsia-400">INR 8,500</span>
            </div>
        </div>
    </section>

    <!-- Booking Form -->
    <section id="book" class="bg-zinc-900 border-t border-zinc-800 py-20">
        <div class="max-w-md mx-auto px-6 bg-zinc-950 border border-zinc-800 rounded-2xl p-8">
            <h2 class="text-xl font-bold text-white text-center mb-6">Select Appointment Slot</h2>
            <form onsubmit="event.preventDefault(); alert('Booking registered. We will call you back to confirm!');" class="space-y-4 text-xs">
                <div>
                    <label class="block text-zinc-400 mb-1">Your Name</label>
                    <input type="text" required class="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-zinc-400 mb-1">Date</label>
                        <input type="date" required class="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white">
                    </div>
                    <div>
                        <label class="block text-zinc-400 mb-1">Service Type</label>
                        <select class="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white">
                            <option>Haircut & Styling</option>
                            <option>Color Treatments</option>
                            <option>Hydrafacials</option>
                            <option>Premium Grooming</option>
                        </select>
                    </div>
                </div>
                <button type="submit" class="w-full py-3 bg-fuchsia-600 text-white font-bold rounded-xl hover:bg-fuchsia-700 transition">Request Slot</button>
            </form>
        </div>
    </section>

    <footer class="py-12 border-t border-zinc-800 text-center text-xs text-zinc-500">
        <p class="text-white font-bold mb-2">{name}</p>
        <p>{addr} | {phone} | {email}</p>
        <p class="mt-4">&copy; 2026 {name}. Glow beautifully.</p>
    </footer>
</body>
</html>
"""


def _get_dentist_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    {_get_base_head(name, "Outfit")}
</head>
<body class="bg-zinc-50 text-zinc-700">
    <header class="border-b border-zinc-200 bg-white sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <span class="font-extrabold text-blue-600 text-xl tracking-tight">🦷 {name}</span>
            <a href="#consult" class="px-5 py-2 bg-blue-600 text-white font-bold text-xs rounded-full hover:bg-blue-700 transition">Request Consultation</a>
        </div>
    </header>

    <!-- Hero -->
    <section class="bg-blue-50 py-24 text-center">
        <div class="max-w-3xl mx-auto px-6">
            <span class="text-blue-600 text-xs font-bold uppercase tracking-wider">Expert Oral Care Services</span>
            <h1 class="text-3xl md:text-5xl font-extrabold text-zinc-900 mt-4 leading-tight">Advanced Dentistry & Smile Designing</h1>
            <p class="text-zinc-600 mt-4 text-base">Your family's partner for modern, painless dental care. Providing root canals, implants, and orthodontic aligners in {city}.</p>
            <div class="mt-8">
                <a href="#consult" class="px-8 py-3 bg-blue-600 text-white font-bold text-sm rounded-full hover:bg-blue-700 transition">Schedule Appointment</a>
            </div>
        </div>
    </section>

    <!-- Services -->
    <section class="max-w-5xl mx-auto px-6 py-16">
        <h2 class="text-2xl font-bold text-zinc-900 text-center mb-12">Our Specialized Diagnostics</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="p-6 bg-white border border-zinc-200 rounded-2xl shadow-sm">
                <span class="text-xl">🦷</span>
                <h3 class="font-bold text-zinc-900 mt-3 text-sm">Painless Root Canal</h3>
                <p class="text-xs text-zinc-500 mt-1">Laser-guided advanced treatment to relieve toothaches and preserve healthy structures.</p>
            </div>
            <div class="p-6 bg-white border border-zinc-200 rounded-2xl shadow-sm">
                <span class="text-xl">✨</span>
                <h3 class="font-bold text-zinc-900 mt-3 text-sm">Clear Aligners</h3>
                <p class="text-xs text-zinc-500 mt-1">Invisible orthodontic aligners for teeth straightening without braces metallic wires.</p>
            </div>
            <div class="p-6 bg-white border border-zinc-200 rounded-2xl shadow-sm">
                <span class="text-xl">🏥</span>
                <h3 class="font-bold text-zinc-900 mt-3 text-sm">Dental Implants</h3>
                <p class="text-xs text-zinc-500 mt-1">Permanent biological replacements for missing teeth anchored to structural jawlines.</p>
            </div>
        </div>
    </section>

    <!-- Appointment form -->
    <section id="consult" class="bg-zinc-100 py-16 border-t border-zinc-200">
        <div class="max-w-md mx-auto px-6 bg-white border border-zinc-200 rounded-2xl p-8 shadow-md">
            <h2 class="text-xl font-bold text-zinc-900 text-center mb-6">Request Dental Slot</h2>
            <form onsubmit="event.preventDefault(); alert('Appointment requested. We will contact you shortly!');" class="space-y-4 text-xs">
                <div>
                    <label class="block text-zinc-600 mb-1">Full Name</label>
                    <input type="text" required class="w-full bg-zinc-50 border border-zinc-300 rounded-lg p-2.5">
                </div>
                <div>
                    <label class="block text-zinc-600 mb-1">Phone Number</label>
                    <input type="tel" required class="w-full bg-zinc-50 border border-zinc-300 rounded-lg p-2.5">
                </div>
                <button type="submit" class="w-full py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition">Request Slot</button>
            </form>
        </div>
    </section>

    <footer class="py-12 bg-white border-t border-zinc-200 text-center text-xs text-zinc-400">
        <p class="text-zinc-900 font-bold mb-1">{name}</p>
        <p>{addr} | {phone} | {email}</p>
        <p class="mt-4">&copy; 2026 {name}. Smile with confidence.</p>
    </footer>
</body>
</html>
"""


def _get_clinic_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    {_get_base_head(name, "Outfit")}
</head>
<body class="bg-zinc-50 text-zinc-700">
    <header class="border-b border-zinc-200 bg-white sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <span class="font-extrabold text-emerald-600 text-xl tracking-tight">🏥 {name}</span>
            <a href="#appointment" class="px-5 py-2 bg-emerald-600 text-white font-bold text-xs rounded-full hover:bg-emerald-700 transition">Schedule Visit</a>
        </div>
    </header>

    <section class="bg-emerald-50 py-24 text-center">
        <div class="max-w-3xl mx-auto px-6">
            <span class="text-emerald-600 text-xs font-bold uppercase tracking-wider">Compassionate Medical Care</span>
            <h1 class="text-3xl md:text-5xl font-extrabold text-zinc-900 mt-4 leading-tight">Your Health, Our Top Priority</h1>
            <p class="text-zinc-600 mt-4 text-base">Providing complete family medicine, pediatrics, and diagnostic checks. Dedicated specialist doctors consulting in {city}.</p>
            <div class="mt-8">
                <a href="#appointment" class="px-8 py-3 bg-emerald-600 text-white font-bold text-sm rounded-full hover:bg-emerald-700 transition">Book Consult</a>
            </div>
        </div>
    </section>

    <!-- Appointment form -->
    <section id="appointment" class="bg-zinc-100 py-16">
        <div class="max-w-md mx-auto px-6 bg-white border border-zinc-200 rounded-2xl p-8 shadow-md">
            <h2 class="text-xl font-bold text-zinc-900 text-center mb-6">Book Consultation</h2>
            <form onsubmit="event.preventDefault(); alert('Booking received. A clinic coordinator will call you to confirm!');" class="space-y-4 text-xs">
                <div>
                    <label class="block text-zinc-600 mb-1">Patient Name</label>
                    <input type="text" required class="w-full bg-zinc-50 border border-zinc-300 rounded-lg p-2.5">
                </div>
                <div>
                    <label class="block text-zinc-600 mb-1">Select Specialty</label>
                    <select class="w-full bg-zinc-50 border border-zinc-300 rounded-lg p-2.5">
                        <option>General Medicine</option>
                        <option>Pediatrics</option>
                        <option>Physiotherapy & Rehab</option>
                        <option>Cardiology Checkup</option>
                    </select>
                </div>
                <button type="submit" class="w-full py-3 bg-emerald-600 text-white font-bold rounded-lg hover:bg-emerald-700 transition">Book Visit Slot</button>
            </form>
        </div>
    </section>

    <footer class="py-12 bg-white border-t border-zinc-200 text-center text-xs text-zinc-400">
        <p class="text-zinc-900 font-bold mb-1">{name}</p>
        <p>{addr} | {phone} | {email}</p>
        <p class="mt-4">&copy; 2026 {name}. Dedicated to care.</p>
    </footer>
</body>
</html>
"""


def _get_school_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    {_get_base_head(name, "Outfit")}
</head>
<body class="bg-zinc-50 text-zinc-700">
    <header class="border-b border-zinc-200 bg-white sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <span class="font-extrabold text-indigo-700 text-xl tracking-tight">🎓 {name}</span>
            <a href="#enroll" class="px-5 py-2 bg-indigo-700 text-white font-bold text-xs rounded-full hover:bg-indigo-800 transition">Admissions 2026-27</a>
        </div>
    </header>

    <section class="bg-indigo-50 py-24 text-center">
        <div class="max-w-3xl mx-auto px-6">
            <span class="text-indigo-600 text-xs font-bold uppercase tracking-wider">Inspiring Lifelong Learners</span>
            <h1 class="text-3xl md:text-5xl font-extrabold text-zinc-900 mt-4 leading-tight">Shaping the Future Leaders</h1>
            <p class="text-zinc-600 mt-4 text-base">Comprehensive co-educational curriculum with a focus on sports, arts, technology, and character development in {city}.</p>
            <div class="mt-8">
                <a href="#enroll" class="px-8 py-3 bg-indigo-700 text-white font-bold text-sm rounded-full hover:bg-indigo-800 transition">Enroll Now</a>
            </div>
        </div>
    </section>

    <!-- Admissions Form -->
    <section id="enroll" class="bg-zinc-100 py-16">
        <div class="max-w-md mx-auto px-6 bg-white border border-zinc-200 rounded-2xl p-8 shadow-md">
            <h2 class="text-xl font-bold text-zinc-900 text-center mb-6">Admissions Inquiry</h2>
            <form onsubmit="event.preventDefault(); alert('Thank you! Admissions Office will mail you the brochure and schedule a campus tour!');" class="space-y-4 text-xs">
                <div>
                    <label class="block text-zinc-600 mb-1">Parent's Name</label>
                    <input type="text" required class="w-full bg-zinc-50 border border-zinc-300 rounded-lg p-2.5">
                </div>
                <div>
                    <label class="block text-zinc-600 mb-1">Child's Grade / Class</label>
                    <select class="w-full bg-zinc-50 border border-zinc-300 rounded-lg p-2.5">
                        <option>Pre-School / Kindergarten</option>
                        <option>Primary School (Grades 1-5)</option>
                        <option>Middle School (Grades 6-8)</option>
                        <option>High School (Grades 9-12)</option>
                    </select>
                </div>
                <button type="submit" class="w-full py-3 bg-indigo-700 text-white font-bold rounded-lg hover:bg-indigo-800 transition">Submit Inquiry</button>
            </form>
        </div>
    </section>

    <footer class="py-12 bg-white border-t border-zinc-200 text-center text-xs text-zinc-400">
        <p class="text-zinc-900 font-bold mb-1">{name}</p>
        <p>{addr} | {phone} | {email}</p>
        <p class="mt-4">&copy; 2026 {name}. Excellence in learning.</p>
    </footer>
</body>
</html>
"""


def _get_realestate_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    {_get_base_head(name, "Outfit")}
</head>
<body class="bg-zinc-950 text-zinc-300">
    <header class="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <span class="font-extrabold text-white text-xl tracking-tight">🏢 {name.upper()}</span>
            <a href="#inquire" class="px-5 py-2.5 bg-amber-500 text-zinc-950 font-bold text-xs rounded-xl hover:bg-amber-600 transition">Find Property</a>
        </div>
    </header>

    <section class="relative bg-zinc-900 py-32 text-center overflow-hidden">
        <div class="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1564013799919-ab600027ffc6?q=80&w=1200')] bg-cover bg-center opacity-25"></div>
        <div class="relative max-w-4xl mx-auto px-6">
            <span class="text-amber-400 text-xs font-bold uppercase tracking-wider">Premium Property Advisors</span>
            <h1 class="text-4xl md:text-6xl font-black text-white mt-6 leading-tight">Find Your Dream Space</h1>
            <p class="text-zinc-300 mt-4 text-base max-w-2xl mx-auto">Discover luxury residences, commercial office spaces, and industrial projects in {city} curated specifically for your lifestyle.</p>
            <div class="mt-8">
                <a href="#inquire" class="px-8 py-4 bg-amber-500 text-zinc-950 font-bold text-sm rounded-xl hover:bg-amber-600 transition">Get Consultant Call</a>
            </div>
        </div>
    </section>

    <!-- Form -->
    <section id="inquire" class="bg-zinc-900 border-t border-zinc-800 py-20">
        <div class="max-w-md mx-auto px-6 bg-zinc-950 border border-zinc-800 rounded-2xl p-8">
            <h2 class="text-xl font-bold text-white text-center mb-6">Property Request Form</h2>
            <form onsubmit="event.preventDefault(); alert('Consultant matching search criteria will call you in 30 mins!');" class="space-y-4 text-xs">
                <div>
                    <label class="block text-zinc-400 mb-1">Your Name</label>
                    <input type="text" required class="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-zinc-400 mb-1">Budget Range</label>
                        <select class="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white">
                            <option>50L - 1 Cr</option>
                            <option>1 Cr - 3 Cr</option>
                            <option>3 Cr - 5 Cr</option>
                            <option>5 Cr+</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-zinc-400 mb-1">Type</label>
                        <select class="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white">
                            <option>Residential Apartment</option>
                            <option>Luxury Villa</option>
                            <option>Commercial Space</option>
                        </select>
                    </div>
                </div>
                <button type="submit" class="w-full py-3 bg-amber-500 text-zinc-950 font-bold rounded-xl hover:bg-amber-600 transition">Match Properties</button>
            </form>
        </div>
    </section>

    <footer class="py-12 border-t border-zinc-800 text-center text-xs text-zinc-500">
        <p class="text-white font-bold mb-2">{name}</p>
        <p>{addr} | {phone} | {email}</p>
        <p class="mt-4">&copy; 2026 {name}. Find home.</p>
    </footer>
</body>
</html>
"""


def _get_corporate_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    {_get_base_head(name, "Outfit")}
</head>
<body class="bg-zinc-950 text-zinc-300">
    <header class="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <span class="font-extrabold text-white text-xl tracking-tight">🏢 {name}</span>
            <a href="#contact" class="px-5 py-2.5 bg-indigo-600 text-white font-bold text-xs rounded-xl hover:bg-indigo-700 transition">Get in Touch</a>
        </div>
    </header>

    <section class="relative bg-zinc-900 py-32 text-center overflow-hidden">
        <div class="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1200')] bg-cover bg-center opacity-25"></div>
        <div class="relative max-w-4xl mx-auto px-6">
            <span class="text-indigo-400 text-xs font-bold uppercase tracking-wider">Enterprise Business Consulting</span>
            <h1 class="text-4xl md:text-6xl font-black text-white mt-6 leading-tight">{name}</h1>
            <p class="text-zinc-300 mt-4 text-base max-w-2xl mx-auto">Helping modern industries scale operational bandwidth through custom engineered SaaS & software infrastructures in {city}.</p>
            <div class="mt-8">
                <a href="#contact" class="px-8 py-4 bg-indigo-600 text-white font-bold text-sm rounded-xl hover:bg-indigo-700 transition">Schedule Strategy Session</a>
            </div>
        </div>
    </section>

    <!-- Form -->
    <section id="contact" class="bg-zinc-900 border-t border-zinc-800 py-20">
        <div class="max-w-md mx-auto px-6 bg-zinc-950 border border-zinc-800 rounded-2xl p-8">
            <h2 class="text-xl font-bold text-white text-center mb-6">Contact Representative</h2>
            <form onsubmit="event.preventDefault(); alert('Query submitted. A specialist will follow up in 2 hours!');" class="space-y-4 text-xs">
                <div>
                    <label class="block text-zinc-400 mb-1">Company / Your Name</label>
                    <input type="text" required class="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white">
                </div>
                <div>
                    <label class="block text-zinc-400 mb-1">Email Address</label>
                    <input type="email" required class="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-white">
                </div>
                <button type="submit" class="w-full py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition">Send Inquiry</button>
            </form>
        </div>
    </section>

    <footer class="py-12 border-t border-zinc-800 text-center text-xs text-zinc-500">
        <p class="text-white font-bold mb-2">{name}</p>
        <p>{addr} | {phone} | {email}</p>
        <p class="mt-4">&copy; 2026 {name}. Driving innovation forward.</p>
    </footer>
</body>
</html>
"""


def _get_hospital_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    head = _get_base_head(name, "Inter")
    return f"""<!DOCTYPE html>
<html>
<head>
    {head}
</head>
<body class="bg-slate-50 text-slate-800">
    <!-- Header -->
    <header class="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-slate-100 py-4 px-6 flex justify-between items-center">
        <span class="text-lg font-bold text-sky-600 tracking-tight">🏥 {name}</span>
        <a href="#appointment" class="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-full text-xs font-semibold shadow-md transition">Book Consultation</a>
    </header>

    <!-- Hero -->
    <section class="pt-32 pb-20 px-6 max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
        <div>
            <span class="text-xs font-bold text-sky-600 bg-sky-50 px-3 py-1 rounded-full uppercase tracking-wider">World-Class Healthcare</span>
            <h1 class="text-4xl md:text-5xl font-extrabold text-slate-900 leading-tight mt-4">Advanced Medical Care, Closer To You.</h1>
            <p class="text-sm text-slate-500 mt-6 leading-relaxed">Providing premium treatment protocols, expert diagnostics, and inpatient emergency services round the clock in {city}.</p>
            <div class="mt-8 flex gap-4">
                <a href="#appointment" class="px-6 py-3 bg-sky-600 text-white font-bold rounded-xl text-xs hover:bg-sky-700 transition">Online Booking</a>
                <a href="tel:{phone}" class="px-6 py-3 bg-slate-100 text-slate-700 font-bold rounded-xl text-xs hover:bg-slate-200 transition">Emergency Call</a>
            </div>
        </div>
        <div class="relative bg-gradient-to-tr from-sky-100 to-indigo-100 h-80 rounded-3xl border border-sky-100 flex items-center justify-center p-8 text-center">
            <div>
                <p class="text-5xl">🧑‍⚕️</p>
                <h3 class="text-xl font-bold text-slate-900 mt-4">24/7 Medical Care</h3>
                <p class="text-xs text-slate-500 mt-2">Accredited clinics with advanced intensive treatment wards.</p>
            </div>
        </div>
    </section>

    <!-- Specialties -->
    <section class="py-20 bg-white border-y border-slate-100">
        <div class="max-w-5xl mx-auto px-6">
            <h2 class="text-2xl font-bold text-slate-900 text-center mb-12">Our Specialized Clinics</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="p-6 bg-slate-50 border border-slate-100 rounded-2xl hover:shadow-lg transition">
                    <p class="text-3xl">🫀</p>
                    <h3 class="font-bold text-slate-900 mt-4">Cardiology</h3>
                    <p class="text-xs text-slate-500 mt-2">Comprehensive screening, ECG tests, and critical heart surgeries.</p>
                </div>
                <div class="p-6 bg-slate-50 border border-slate-100 rounded-2xl hover:shadow-lg transition">
                    <p class="text-3xl">🧠</p>
                    <h3 class="font-bold text-slate-900 mt-4">Neurology</h3>
                    <p class="text-xs text-slate-500 mt-2">Brain mapping, therapeutic intervention, and nerve diagnosis.</p>
                </div>
                <div class="p-6 bg-slate-50 border border-slate-100 rounded-2xl hover:shadow-lg transition">
                    <p class="text-3xl">🦴</p>
                    <h3 class="font-bold text-slate-900 mt-4">Orthopedics</h3>
                    <p class="text-xs text-slate-500 mt-2">Joint replacements, fracture correction, and advanced physical therapy.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Appointment Form -->
    <section id="appointment" class="py-20 bg-slate-50">
        <div class="max-w-md mx-auto px-6 bg-white border border-slate-100 rounded-3xl p-8 shadow-sm">
            <h2 class="text-xl font-bold text-slate-900 text-center mb-6">Book OPD Consultation</h2>
            <form onsubmit="event.preventDefault(); alert('Appointment requested! Our front desk will text your confirmation ID in 5 minutes.');" class="space-y-4 text-xs">
                <div>
                    <label class="block text-slate-500 mb-1">Patient Full Name</label>
                    <input type="text" required class="w-full border border-slate-200 rounded-xl p-3 text-slate-800 focus:outline-sky-500">
                </div>
                <div>
                    <label class="block text-slate-500 mb-1">Preferred Clinic Department</label>
                    <select class="w-full border border-slate-200 rounded-xl p-3 text-slate-800 focus:outline-sky-500">
                        <option>General OPD Checkup</option>
                        <option>Cardiology Specialist</option>
                        <option>Neurology Specialist</option>
                        <option>Orthopedic Diagnostics</option>
                    </select>
                </div>
                <button type="submit" class="w-full py-3.5 bg-sky-600 text-white font-bold rounded-xl hover:bg-sky-700 transition">Request Appointment Slots</button>
            </form>
        </div>
    </section>

    <footer class="py-12 bg-slate-900 text-slate-400 text-center text-xs">
        <p class="text-white font-bold mb-2">{name}</p>
        <p>{addr} | {phone} | {email}</p>
        <p class="mt-4">&copy; 2026 {name}. Dedicated to healthcare excellence.</p>
    </footer>
</body>
</html>
"""


def _get_lawyer_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    head = _get_base_head(name, "Playfair Display")
    return f"""<!DOCTYPE html>
<html>
<head>
    {head}
    <style>
        .bronze-glow {{
            text-shadow: 0 0 10px rgba(197, 160, 89, 0.2);
        }}
    </style>
</head>
<body class="bg-stone-950 text-stone-300">
    <!-- Header -->
    <header class="fixed top-0 w-full z-50 bg-stone-950/90 border-b border-stone-850 py-5 px-8 flex justify-between items-center">
        <span class="text-lg font-serif font-bold text-amber-500 tracking-wider bronze-glow">⚖️ {name.upper()}</span>
        <a href="#consultation" class="px-5 py-2.5 border border-amber-500/50 hover:bg-amber-500 hover:text-stone-950 text-amber-500 text-xs font-serif uppercase tracking-widest transition">Schedule Audit</a>
    </header>

    <!-- Hero -->
    <section class="pt-40 pb-24 px-8 max-w-5xl mx-auto text-center">
        <span class="text-xs uppercase tracking-widest text-amber-500">Experienced Legal Advisory</span>
        <h1 class="text-4xl md:text-6xl font-serif font-extrabold text-white mt-6 leading-tight">Advocating For Your Rights in {city}.</h1>
        <p class="text-sm text-stone-400 max-w-xl mx-auto mt-6 leading-relaxed">Providing sophisticated corporate defense, intellectual property litigation, and private client representation services.</p>
        <div class="mt-10 flex justify-center gap-6">
            <a href="#consultation" class="px-8 py-3.5 bg-amber-500 text-stone-950 font-bold uppercase tracking-widest text-[10px] hover:bg-amber-600 transition">Book Strategy Session</a>
            <a href="tel:{phone}" class="px-8 py-3.5 border border-stone-700 text-white font-bold uppercase tracking-widest text-[10px] hover:bg-stone-900 transition">Direct Line</a>
        </div>
    </section>

    <!-- Practice Areas -->
    <section class="py-24 bg-stone-900 border-y border-stone-850">
        <div class="max-w-5xl mx-auto px-8">
            <h2 class="text-3xl font-serif text-white text-center mb-16">Areas of Legal Practice</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-10">
                <div class="p-8 bg-stone-950 border border-stone-800 rounded-lg hover:border-amber-500/40 transition">
                    <h3 class="font-serif text-lg text-amber-500 mb-4">Corporate & Tax law</h3>
                    <p class="text-xs text-stone-400 leading-relaxed">Handling regulatory filings, commercial corporate transitions, audits, and international compliance structures.</p>
                </div>
                <div class="p-8 bg-stone-950 border border-stone-800 rounded-lg hover:border-amber-500/40 transition">
                    <h3 class="font-serif text-lg text-amber-500 mb-4">Intellectual Property</h3>
                    <p class="text-xs text-stone-400 leading-relaxed">Securing core innovation designs, digital patent protections, trademark registration, and litigation.</p>
                </div>
                <div class="p-8 bg-stone-950 border border-stone-800 rounded-lg hover:border-amber-500/40 transition">
                    <h3 class="font-serif text-lg text-amber-500 mb-4">Litigation Defense</h3>
                    <p class="text-xs text-stone-400 leading-relaxed">High-stakes commercial litigation, contract disputes, intellectual properties recovery, and court appeals.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Consultation Form -->
    <section id="consultation" class="py-24 bg-stone-950">
        <div class="max-w-md mx-auto px-8 bg-stone-900 border border-stone-800 rounded-xl p-10 shadow-xl">
            <h2 class="text-2xl font-serif text-white text-center mb-6">Request Legal Evaluation</h2>
            <form onsubmit="event.preventDefault(); alert('Evaluation request received. Our counsel assistant will contact you in 4 hours.');" class="space-y-4 text-xs">
                <div>
                    <label class="block text-stone-400 mb-1 font-serif uppercase tracking-wider">Client Name</label>
                    <input type="text" required class="w-full bg-stone-950 border border-stone-800 rounded p-3 text-white focus:outline-none focus:border-amber-500">
                </div>
                <div>
                    <label class="block text-stone-400 mb-1 font-serif uppercase tracking-wider">Case description summary</label>
                    <textarea required rows="3" class="w-full bg-stone-950 border border-stone-800 rounded p-3 text-white focus:outline-none focus:border-amber-500"></textarea>
                </div>
                <button type="submit" class="w-full py-3.5 bg-amber-500 text-stone-950 font-serif font-bold uppercase tracking-widest text-[10px] hover:bg-amber-600 transition">Request Consultation</button>
            </form>
        </div>
    </section>

    <footer class="py-16 bg-stone-950 border-t border-stone-850 text-stone-500 text-center text-xs">
        <p class="text-white font-serif uppercase tracking-widest text-amber-500 mb-3">{name}</p>
        <p>{addr} | {phone} | {email}</p>
        <p class="mt-6">&copy; 2026 {name}. Premium Counselors. All rights reserved.</p>
    </footer>
</body>
</html>
"""


def _get_ecommerce_template(name: str, phone: str, email: str, addr: str, city: str) -> str:
    head = _get_base_head(name, "Outfit")
    return f"""<!DOCTYPE html>
<html>
<head>
    {head}
</head>
<body class="bg-zinc-50 text-zinc-800">
    <!-- Header -->
    <header class="fixed top-0 w-full z-50 bg-white/90 border-b border-zinc-100 py-4 px-8 flex justify-between items-center">
        <span class="text-lg font-bold text-zinc-950 tracking-tight">🛍️ {name}</span>
        <div class="flex items-center gap-4">
            <span class="text-xs bg-zinc-100 px-3 py-1 rounded-full font-bold">🛒 Cart (3)</span>
            <a href="#products" class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition">Shop Now</a>
        </div>
    </header>

    <!-- Hero -->
    <section class="pt-36 pb-20 px-8 max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
        <div>
            <span class="text-xs font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full uppercase tracking-wider">Fast Shipping in {city}</span>
            <h1 class="text-4xl md:text-5xl font-extrabold text-zinc-950 leading-tight mt-4">Curated Premium Goods, Built to Last.</h1>
            <p class="text-sm text-zinc-500 mt-6 leading-relaxed">Discover high-quality essentials crafted for modern living. Get 20% off plus free shipping on your first purchase today.</p>
            <div class="mt-8">
                <a href="#products" class="px-6 py-3.5 bg-emerald-600 text-white font-bold rounded-xl text-xs hover:bg-emerald-700 transition">View Catalog</a>
            </div>
        </div>
        <div class="bg-gradient-to-tr from-emerald-100 to-cyan-100 h-80 rounded-3xl flex items-center justify-center p-8 relative overflow-hidden">
            <div class="text-center">
                <span class="text-6xl">🎁</span>
                <h3 class="text-xl font-bold text-zinc-950 mt-4">Apex Premium Box</h3>
                <p class="text-xs text-zinc-500 mt-1">Starting from ₹1,299</p>
            </div>
        </div>
    </section>

    <!-- Product Grid -->
    <section id="products" class="py-24 bg-white border-y border-zinc-100">
        <div class="max-w-5xl mx-auto px-8">
            <h2 class="text-2xl font-bold text-zinc-950 text-center mb-16">Trending Essentials</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="border border-zinc-100 rounded-2xl overflow-hidden hover:shadow-lg transition">
                    <div class="bg-zinc-100 h-48 flex items-center justify-center text-4xl">👜</div>
                    <div class="p-6">
                        <span class="text-[10px] font-bold text-zinc-400 uppercase">Lifestyle</span>
                        <h3 class="font-bold text-zinc-950 mt-1">Leather Work Tote</h3>
                        <p class="text-sm text-emerald-600 font-bold mt-2">₹3,499</p>
                        <button onclick="alert('Item added to cart!');" class="w-full mt-4 py-2 border border-zinc-200 text-zinc-700 rounded-lg text-xs font-bold hover:bg-zinc-50 transition">Add to Cart</button>
                    </div>
                </div>
                <div class="border border-zinc-100 rounded-2xl overflow-hidden hover:shadow-lg transition">
                    <div class="bg-zinc-100 h-48 flex items-center justify-center text-4xl">🎧</div>
                    <div class="p-6">
                        <span class="text-[10px] font-bold text-zinc-400 uppercase">Acoustics</span>
                        <h3 class="font-bold text-zinc-950 mt-1">Active ANC Earphones</h3>
                        <p class="text-sm text-emerald-600 font-bold mt-2">₹7,999</p>
                        <button onclick="alert('Item added to cart!');" class="w-full mt-4 py-2 border border-zinc-200 text-zinc-700 rounded-lg text-xs font-bold hover:bg-zinc-50 transition">Add to Cart</button>
                    </div>
                </div>
                <div class="border border-zinc-100 rounded-2xl overflow-hidden hover:shadow-lg transition">
                    <div class="bg-zinc-100 h-48 flex items-center justify-center text-4xl">🕶️</div>
                    <div class="p-6">
                        <span class="text-[10px] font-bold text-zinc-400 uppercase">Apparel</span>
                        <h3 class="font-bold text-zinc-950 mt-1">polarized acetate shades</h3>
                        <p class="text-sm text-emerald-600 font-bold mt-2">₹1,899</p>
                        <button onclick="alert('Item added to cart!');" class="w-full mt-4 py-2 border border-zinc-200 text-zinc-700 rounded-lg text-xs font-bold hover:bg-zinc-50 transition">Add to Cart</button>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Newsletter Form -->
    <section class="py-24 bg-zinc-50">
        <div class="max-w-md mx-auto px-8 text-center">
            <h2 class="text-xl font-bold text-zinc-950 mb-2">Subscribe to VIP Catalog Drops</h2>
            <p class="text-xs text-zinc-500 mb-6">Receive early notifications of collections and exclusive local shipping deals.</p>
            <form onsubmit="event.preventDefault(); alert('Welcome to the VIP club! Check your inbox for a 20% discount code.');" class="flex gap-2">
                <input type="email" required placeholder="Enter email address" class="w-full px-4 border border-zinc-200 rounded-xl text-xs focus:outline-emerald-500">
                <button type="submit" class="px-5 py-3 bg-emerald-600 text-white font-bold rounded-xl text-xs hover:bg-emerald-700 transition">Join</button>
            </form>
        </div>
    </section>

    <footer class="py-16 bg-zinc-900 text-zinc-400 text-center text-xs">
        <p class="text-white font-bold mb-2">{name}</p>
        <p>{addr} | {phone} | {email}</p>
        <p class="mt-4">&copy; 2026 {name}. Premium Retail. All rights reserved.</p>
    </footer>
</body>
</html>
"""

