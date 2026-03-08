"""
Marc Planas — Insurtech Professional Profile
Used by job_hunter.py to score and match job listings.
"""

PROFILE = {
    "name": "Marc Planas",
    "email": "marcplanas11@gmail.com",
    "languages": ["English", "Spanish", "Catalan"],
    "location": "Barcelona, Spain (open to fully remote EU roles)",

    "target_roles": [
        "Operations", "Consulting", "Product", "Strategy",
        "Tech", "Engineering", "MGA", "Insurtech", "Underwriting Operations",
        "Business Development", "Account Management", "InsurTech Consultant"
    ],

    "experience": [
        {
            "title": "Insurance / Insurtech Professional",
            "domain": "Insurance, MGA, Insurtech",
            "skills": [
                "insurance operations", "MGA management", "underwriting",
                "product strategy", "digital transformation", "insurtech platforms",
                "claims management", "broker relationships", "Lloyd's market",
                "parametric insurance", "embedded insurance", "API integrations",
                "process automation", "stakeholder management", "P&L management"
            ]
        }
    ],

    "technical_skills": [
        "Python", "GitHub Actions", "APIs", "data analysis",
        "CRM systems", "insurance platforms", "digital tools"
    ],

    "keywords_high_priority": [
        "insurtech", "MGA", "Lloyd's", "parametric", "embedded insurance",
        "insurance platform", "underwriting", "digital insurance",
        "insurance operations", "insurtech consultant"
    ],

    "keywords_medium_priority": [
        "fintech", "healthtech", "SaaS", "B2B", "operations manager",
        "product manager", "business development", "account manager",
        "remote", "consultant", "strategy"
    ],

    "keywords_exclude": [
        "junior", "graduate", "intern", "entry level", "apprentice"
    ],

    "preferred_work": "fully remote",
    "preferred_regions": ["EU", "UK", "Spain", "Remote"],
    "min_match_score": 80,

    "cv_summary_en": """
Experienced Insurance and Insurtech professional with a strong background in
insurance operations, MGA management, digital transformation, and insurtech platforms.
Proven ability to drive operational excellence, build broker and partner relationships,
and deliver product and strategy initiatives in fast-growing insurtech environments.
Bilingual in English and Spanish. Open to remote roles across the EU and UK.
""",

    "cv_summary_es": """
Profesional con amplia experiencia en seguros e insurtech, especializado en operaciones
de seguros, gestión de MGAs, transformación digital y plataformas insurtech.
Trayectoria demostrada en excelencia operacional, relaciones con brokers y socios,
e iniciativas de producto y estrategia en entornos insurtech de alto crecimiento.
Bilingüe en inglés y español. Disponible para trabajar de forma remota en la UE y UK.
""",
}
