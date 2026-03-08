"""
Marc Planas — Insurtech Professional Profile
Used by job_hunter.py to score and match job listings.
"""

PROFILE = {
    "name": "Marc Planas",
    "email": "marcplanas11@gmail.com",
    "languages": ["English", "Spanish", "Catalan"],
    "location": "Barcelona, Spain",

    # ── Location & Work Preferences ──────────────────────────────
    "location_preferences": {
        "remote_eu": True,           # fully remote anywhere in EU ✅
        "hybrid_barcelona": True,    # hybrid roles based in Barcelona ✅
        "hybrid_other": False,       # hybrid outside Barcelona ❌
        "onsite_only": False,        # on-site only roles ❌
        "outside_eu": False,         # roles outside EU ❌
    },

    # ── Salary ───────────────────────────────────────────────────
    "min_salary_eur": 60000,
    "salary_note": "Minimum €60,000 EUR/year. Roles without salary info still considered.",

    # ── Target Roles ─────────────────────────────────────────────
    "target_roles": [
        "Operations", "Consulting", "Product", "Strategy",
        "Tech", "Engineering", "MGA", "Insurtech", "Underwriting Operations",
        "Business Development", "Account Management", "InsurTech Consultant"
    ],

    # ── Domain Experience ─────────────────────────────────────────
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

    # ── Technical Skills ─────────────────────────────────────────
    "technical_skills": [
        "Python", "SQL", "Agile", "Scrum",
        "Excel", "Data Analysis", "CRM Systems",
        "GitHub Actions", "APIs", "insurance platforms"
    ],

    # ── Scoring Keywords ─────────────────────────────────────────
    "keywords_high_priority": [
        "insurtech", "MGA", "Lloyd's", "parametric", "embedded insurance",
        "insurance platform", "underwriting", "digital insurance",
        "insurance operations", "insurtech consultant",
        "agile", "scrum", "SQL", "python", "data analysis"
    ],

    "keywords_medium_priority": [
        "fintech", "healthtech", "SaaS", "B2B", "operations manager",
        "product manager", "business development", "account manager",
        "remote", "consultant", "strategy", "excel", "CRM"
    ],

    "keywords_exclude": [
        "junior", "graduate", "intern", "entry level", "apprentice"
    ],

    "min_match_score": 80,

    # ── CV Summaries ─────────────────────────────────────────────
    "cv_summary_en": """
Experienced Insurance and Insurtech professional with a strong background in
insurance operations, MGA management, digital transformation, and insurtech platforms.
Skilled in Python, SQL, Agile/Scrum, Excel, and CRM systems, with proven ability to
drive operational excellence, build broker and partner relationships, and deliver
product and strategy initiatives in fast-growing insurtech environments.
Bilingual in English and Spanish. Open to fully remote EU roles and hybrid roles in Barcelona.
""",

    "cv_summary_es": """
Profesional con amplia experiencia en seguros e insurtech, especializado en operaciones
de seguros, gestión de MGAs, transformación digital y plataformas insurtech.
Con dominio de Python, SQL, metodologías Agile/Scrum, Excel y sistemas CRM, con
trayectoria demostrada en excelencia operacional, relaciones con brokers y socios,
e iniciativas de producto y estrategia en entornos insurtech de alto crecimiento.
Bilingüe en inglés y español. Disponible para trabajo remoto en la UE o híbrido en Barcelona.
""",
}
