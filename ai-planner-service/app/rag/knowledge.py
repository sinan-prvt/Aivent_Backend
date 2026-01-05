from langchain_core.documents import Document

def get_documents():
    return [

        Document(
            page_content="""
EVENT TYPE: Wedding
BUDGET RANGE: Under 3 Lakhs INR
GUEST COUNT: 80–120
CITY TYPE: Tier-2 or Tier-3 city

PRIORITY SERVICES:
- Catering (simple buffet)
- Basic venue decoration
- Community or function hall

DEFERRED SERVICES:
- DJ or live band
- Premium photography
- Luxury lighting

BUDGET BREAKDOWN:
- Catering: 45–50%
- Venue & decoration: 30–35%
- Photography (basic): 10–15%
- Miscellaneous: 5–10%

PLANNING TIPS:
- Prefer lunch wedding
- Limit menu items
- Avoid multiple vendors
"""
        ),

        Document(
            page_content="""
EVENT TYPE: Wedding
BUDGET RANGE: Under 5 Lakhs INR
GUEST COUNT: 100–150
CITY TYPE: Tier-1 or Tier-2 city

PRIORITY SERVICES:
- Catering with expanded menu
- Better stage decoration
- Standard photography & videography

OPTIONAL SERVICES:
- DJ (budget-friendly)
- Enhanced lighting

BUDGET BREAKDOWN:
- Catering: 40–45%
- Venue & decoration: 30%
- Photography & video: 15–20%
- Entertainment & misc: 5–10%

PLANNING TIPS:
- Choose bundled vendor packages
- Limit premium add-ons
"""
        ),

        Document(
            page_content="""
EVENT TYPE: Birthday Party
BUDGET RANGE: Under 50,000 INR
GUEST COUNT: 30–50
VENUE TYPE: Home or small party hall

PRIORITY SERVICES:
- Cake
- Basic decorations
- Snacks and refreshments

DEFERRED SERVICES:
- Live entertainment
- Professional photography

BUDGET BREAKDOWN:
- Food & cake: 40%
- Decorations: 30%
- Venue & misc: 30%

PLANNING TIPS:
- DIY decoration
- Short event duration
"""
        ),
    ]
