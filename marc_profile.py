"""
Marc Planas — Professional Profile for Job Hunter
Reflects actual CV: Operations Data Manager at Accelerant, 10+ years (re)insurance ops.
Used by job_hunter.py to score and match job listings, and generate tailored CVs.
"""

PROFILE = {
    "name": "Marc Planas Callico",
    "email": "marcplanas11@gmail.com",
    "phone": "+34 672 329 911",
    "linkedin": "linkedin.com/in/intlinsure",
    "location": "Barcelona, Spain",

    # ── Languages ────────────────────────────────────────────────
    "languages": [
        {"lang": "English",  "level": "C2"},
        {"lang": "French",   "level": "C1"},
        {"lang": "Spanish",  "level": "Native"},
        {"lang": "Italian",  "level": "B2"},
        {"lang": "Catalan",  "level": "Native"},
    ],

    # ── Location & Work Preferences ──────────────────────────────
    "location_preferences": {
        "remote_eu": True,
        "hybrid_barcelona": True,
        "hybrid_madrid": False,
        "hybrid_other": False,
        "onsite_only": False,
        "outside_eu": False,
    },

    # ── Salary ───────────────────────────────────────────────────
    "min_salary_eur": 60000,
    "target_salary_eur": 75000,
    "salary_note": "Floor €60K, senior target €75K+. Roles without salary info still considered.",

    # ── Target Roles ─────────────────────────────────────────────
    "target_roles": [
        # Traditional Operations (Core)
        "Operations Manager",
        "Insurance Operations Manager",
        "Underwriting Operations Specialist",
        "Underwriting Operations Manager",
        "Insurance Operations Analyst",
        "Head of Operations",
        "Reinsurance Operations",
        "Programme Operations",
        "BPO Manager",
        "Process Excellence Manager",
        "Data Operations Manager",
        # New: AI & Digital Workforce (Expanded Scope)
        "AI Product Engineer",
        "AI Implementation Specialist",
        "Digital Workforce Specialist",
        "AI Operations Specialist",
        "AI-powered Operations Manager",
        "AI/ML Operations Engineer",
        "Automation Engineer (Finance/Insurance)",
    ],

    # ── Target Company Types ─────────────────────────────────────
    "target_company_types": [
        # Traditional Insurance
        "Insurance company",
        "Reinsurance company",
        "Insurtech",
        "MGA (Managing General Agent)",
        "DUA (Delegated Underwriting Authority)",
        "Lloyd's coverholder",
        "Insurance broker",
        "Reinsurance broker",
        "Insurance platform / SaaS",
        # New: AI-Focused & Scale-ups
        "AI-powered InsurTech",
        "AI/ML startup (Finance/Insurance focus)",
        "FinTech with insurance module",
        "AI automation/workflow platform",
        "AI agent orchestration platform",
        "Scale-up (AI + domain expertise)",
    ],

    # ── Domain Experience ─────────────────────────────────────────
    "experience_summary": (
        "Insurance and reinsurance operations professional with 10+ years of experience "
        "owning and improving end-to-end operational processes in MGA, broker and programme "
        "environments. Proven track record managing BPO supplier relationships, drafting and "
        "standardising SOPs, monitoring KPIs/KRIs/SLAs, and acting as primary operational "
        "point of contact for managing agents and external partners. Now building AI agents "
        "and automation tooling (Claude API, LangGraph, CrewAI) to automate the same complex "
        "workflows managed manually for a decade. Certified in Anthropic AI stack (Prompt "
        "Engineering, RAG, Tool Use, Agents, MCP). Experienced in designing processes from "
        "scratch in start-up and scale-up environments."
    ),

    "core_competencies": {
        "operations_process": [
            "End-to-end process ownership",
            "SOP drafting & standardisation",
            "Continuous improvement",
            "BAU management",
            "Submission process management",
            "Account clearance & set-up",
            "Process automation identification",
            "Workflow optimization",
        ],
        "bpo_supplier_management": [
            "BPO oversight",
            "Trainer & referral point",
            "SLA/KPI/KRI monitoring",
            "Performance escalation & resolution",
        ],
        "managing_agent_support": [
            "Operating model implementation",
            "Portfolio analysis",
            "Operational controls",
            "Stakeholder guidance",
            "Delegated underwriting authority monitoring",
        ],
        "compliance_governance": [
            "Solvency II",
            "IFRS 17",
            "Sanctions screening (OFAC, HM Treasury, SDN)",
            "Good Local Standards",
            "Regulatory frameworks",
        ],
        "data_technology": [
            "SQL (intermediate)",
            "Python (intermediate)",
            "Power BI",
            "Snowflake",
            "AI tools (ChatGPT, Claude, Copilot)",
            "Jira",
            "UAT",
            "MS Office & Google Workspace",
        ],
        "ai_automation_stack": [
            "Claude API & Claude.ai",
            "Prompt engineering (CoT, few-shot, XML structuring)",
            "RAG (Retrieval Augmented Generation) concepts",
            "LangChain / LangGraph workflow orchestration",
            "AI agent design & deployment",
            "GitHub Actions automation",
            "CrewAI system design",
            "MCP (Model Context Protocol)",
        ],
        "domain_expertise_translation": [
            "10+ years Finance/Insurance ops knowledge",
            "Identifying AI automation friction points",
            "Business requirement → AI prompt design",
            "Process simplification for AI deployment",
            "Domain-specific validation logic",
            "Compliance & risk assessment for AI systems",
        ],
    },

    "career_history": [
        {
            "title": "Operations Data Manager",
            "company": "Accelerant",
            "type": "MGA Reinsurance Platform",
            "period": "2025–Present",
            "location": "Barcelona / Remote",
            "highlights": [
                "Own end-to-end ops for 20+ managing agent partners across EU and US",
                "BPO supplier trainer and referral point, SLA monitoring",
                "SOP drafting and standardisation across all platform processes",
                "KPI/KRI/SLA monitoring for internal and external performance",
                "Tech supplier collaboration (Intrali): UAT lead, deliverable sign-off",
                "SQL, Power BI, Snowflake for business cases; AI tools for efficiency",
            ],
        },
        {
            "title": "Insurance Program Manager — French Market",
            "company": "Sompo International",
            "type": "Insurer",
            "period": "2024–2025",
            "location": "Barcelona / Paris",
            "highlights": [
                "French market ops end-to-end, primary contact for French-speaking partners",
                "Process documentation, regulatory compliance across French book",
            ],
        },
        {
            "title": "International Programs Operations Specialist",
            "company": "Zurich Insurance Group",
            "type": "Global insurer",
            "period": "2023–2024",
            "location": "Barcelona",
            "highlights": [
                "Governance for 30+ international Commercial Lines programmes",
                "Authority compliance, SLA performance, documentation standards",
                "Training on complex, non-standard scenarios",
            ],
        },
        {
            "title": "International Programs Manager",
            "company": "Confide",
            "type": "Reinsurance Broker",
            "period": "2021–2023",
            "location": "Barcelona",
            "highlights": [
                "Designed processes from scratch for 17 international programmes",
                "SOPs, governance, compliance controls (OFAC, HM Treasury, SDN)",
                "Primary interface: fronting insurers, reinsurers, managing agents, regulators",
            ],
        },
        {
            "title": "Corporate Insurance Advisor & Operations",
            "company": "Riskmedia Insurance Brokers",
            "type": "Broker",
            "period": "2019–2021",
            "location": "Barcelona",
            "highlights": ["End-to-end ops for corporate client portfolio"],
        },
        {
            "title": "Technical Operations — Non-Life",
            "company": "Liberty Seguros",
            "type": "Insurer",
            "period": "2016–2019",
            "location": "Barcelona",
            "highlights": ["Best Efficiency Idea award for CRM workflow redesign"],
        },
        {
            "title": "Insurance Operations",
            "company": "SegurCaixa Adeslas",
            "type": "Insurer (Bancassurance)",
            "period": "2015–2016",
            "location": "Barcelona",
            "highlights": ["Operational management in bancassurance distribution"],
        },
    ],

    "education": [
        {"title": "Corredor de Seguros Grupo B", "institution": "ICEA", "year": "2022"},
        {"title": "PSM I — Professional Scrum Master", "institution": "Scrum.org", "year": "In Progress"},
        {"title": "Agile Project Management", "institution": "Google / Coursera", "year": "In Progress"},
    ],

    # ── Scoring Keywords ─────────────────────────────────────────
    "keywords_high_priority": [
        # Traditional insurance operations
        "insurance operations", "underwriting operations", "reinsurance operations",
        "MGA", "managing general agent", "delegated underwriting", "DUA",
        "Lloyd's", "coverholder", "programme", "program",
        "BPO", "SOP", "KPI", "SLA", "process improvement",
        "Solvency II", "sanctions", "OFAC", "compliance",
        "operations manager", "operations specialist", "operations analyst",
        "insurtech", "insurance platform",
        # New: AI & automation focus
        "AI product engineer", "AI implementation", "digital workforce",
        "AI automation", "workflow automation", "process automation",
        "Claude API", "LLM", "large language model", "generative AI",
        "LangChain", "LangGraph", "agent", "orchestration",
        "prompt engineering", "RAG", "retrieval augmented",
        "AI-powered", "AI-enabled", "automated workflow",
        "finance operations AI", "insurance automation", "claims automation",
        "MCP", "CrewAI", "automation engineer",
    ],

    "keywords_medium_priority": [
        "insurance", "reinsurance", "broker", "underwriting",
        "data operations", "process excellence", "operational excellence",
        "remote", "EU", "Europe", "Barcelona", "Spain",
        "SQL", "Power BI", "Snowflake", "Python",
        "agile", "scrum", "continuous improvement",
        "AI", "machine learning", "automation", "workflow",
        "API", "integration", "data pipeline", "backend",
        "GitHub Actions", "CI/CD", "automation platform",
        "fintech", "finance automation", "treasury operations",
    ],

    "keywords_exclude": [
        "junior", "graduate", "intern", "entry level", "apprentice",
        "pure software engineer", "pure frontend", "pure backend", "pure devops",
        "data scientist (pure ML)", "research scientist",
        "actuary", "actuarial", "pricing analyst",
        "sales agent", "insurance agent", "life insurance agent",
        "claims adjuster", "field adjuster",
    ],

    "min_match_score": 50,

    # ── CV Summaries for AI generation ───────────────────────────
    "cv_summary_en": (
        "Insurance operations professional with 10+ years building complex workflows in MGA, "
        "reinsurance and broker environments. Now architect AI agents and automation systems "
        "(Claude API, LangGraph, CrewAI) to automate the same processes managed manually for "
        "a decade—translating operational domain expertise into production AI systems. Certified "
        "in Anthropic AI stack; fluent in prompt engineering, RAG, agents and MCP. Deep "
        "understanding of Solvency II, sanctions screening (OFAC), regulatory compliance and "
        "operational controls. Bilingual English (C2) / Spanish (native), plus French (C1) "
        "and Italian (B2)."
    ),

    "cv_summary_es": (
        "Profesional de operaciones de seguros con 10+ años diseñando procesos complejos en "
        "entornos MGA, reaseguros y corredores. Ahora construyo agentes AI y sistemas de "
        "automatización (Claude API, LangGraph, CrewAI) para automatizar los mismos procesos "
        "gestionados manualmente durante una década—traduciendo expertise de dominio en "
        "sistemas AI en producción. Certificado en stack Anthropic; experto en prompt "
        "engineering, RAG, agentes y MCP. Conocimiento profundo de Solvencia II, screening "
        "de sanciones, cumplimiento normativo y controles operacionales. Bilingüe inglés "
        "(C2) / español (nativo), más francés (C1) e italiano (B2)."
    ),
}
