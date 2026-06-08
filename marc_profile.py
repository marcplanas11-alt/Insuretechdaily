"""
Marc Planas — Professional Profile for Job Hunter
Reflects current target: EU-wide insurance operations, BA/digital transformation and AI consulting roles.
Used by job_hunter.py to score and match job listings.
"""

PROFILE = {
    "name": "Marc Planas Callico",
    "email": "marcplanas11@gmail.com",
    "phone": "+34 672 329 911",
    "linkedin": "linkedin.com/in/marcplanas11",
    "location": "Barcelona, Spain",

    # ── Languages ────────────────────────────────────────────────
    "languages": [
        {"lang": "English",  "level": "C2"},
        {"lang": "French",   "level": "C1"},
        {"lang": "Spanish",  "level": "Native"},
        {"lang": "Catalan",  "level": "Native"},
        {"lang": "Italian",  "level": "B2"},
    ],

    # ── Location & Work Preferences ──────────────────────────────
    "location_preferences": {
        "remote_eu": True,
        "remote_global_if_eu_eligible": True,
        "hybrid_barcelona": True,
        "hybrid_madrid": False,
        "madrid_presencial": False,
        "eu_relocation_for_ba_consulting": True,
        "eu_relocation_for_ai_consulting": True,
        "hybrid_other_eu_for_strong_ba_roles": True,
        "onsite_only": False,
        "outside_eu": False,
        "notes": (
            "Primary preference is 100% remote EU/EMEA. Barcelona hybrid is acceptable. "
            "EU relocation or hybrid in another European hub is acceptable for strong BA, "
            "digital transformation or AI consulting roles. Madrid presencial remains a hard blocker."
        ),
    },

    # ── Salary ───────────────────────────────────────────────────
    "min_salary_eur": 45000,
    "target_salary_eur": 55000,
    "stretch_salary_eur": 70000,
    "salary_note": (
        "Floor €45K. Target €55K–€70K depending on role, location, remote policy and consulting/insurance fit. "
        "Roles without salary information are still considered."
    ),

    # ── Target Roles ─────────────────────────────────────────────
    "target_roles": [
        # Track A — insurance operations / platforms
        "Operations Manager",
        "Insurance Operations Manager",
        "Insurance Operations Analyst",
        "Underwriting Operations Specialist",
        "Underwriting Operations Manager",
        "Claims Operations Analyst",
        "Claims Transformation Analyst",
        "Reinsurance Operations",
        "Programme Operations",
        "BPO Manager",
        "Process Excellence Manager",
        "Data Operations Manager",
        "Guidewire Business Analyst",
        "Guidewire Consultant",
        "PolicyCenter / ClaimCenter Business Analyst",
        # Track B — BA / transformation / consulting
        "Business Analyst",
        "Senior Business Analyst",
        "IT Business Analyst",
        "Technical Business Analyst",
        "Business Analyst (Insurance)",
        "Business Analyst (InsurTech)",
        "Business Analyst (FinTech)",
        "AI Business Analyst",
        "Digital Transformation Business Analyst",
        "Digital Transformation Consultant",
        "Process Analyst",
        "Business Process Analyst",
        "Implementation Consultant",
        "Functional Consultant",
        "Solution Consultant",
        "Product Owner",
        # Track C — AI consulting / automation
        "AI Consultant",
        "AI Automation Consultant",
        "AI Implementation Consultant",
        "Intelligent Automation Consultant",
        "AI Governance Consultant",
        "Responsible AI Consultant",
        "Digital Workforce Specialist",
        "AI Operations Specialist",
        "AI-powered Operations Manager",
        "Automation Consultant (Finance/Insurance)",
    ],

    # ── Target Company Types ─────────────────────────────────────
    "target_company_types": [
        "Insurance company",
        "Reinsurance company",
        "Insurtech",
        "MGA (Managing General Agent)",
        "DUA (Delegated Underwriting Authority)",
        "Lloyd's coverholder",
        "Insurance broker",
        "Reinsurance broker",
        "Insurance platform / SaaS",
        "Guidewire / Duck Creek / FINEOS consulting partner",
        "AI-powered InsurTech",
        "FinTech with insurance module",
        "AI automation/workflow platform",
        "AI agent orchestration platform",
        "AI governance / compliance platform",
        "Digital transformation consultancy",
        "Business transformation firm",
        "Financial services consulting practice",
        "Insurance advisory practice",
    ],

    # ── Domain Experience ─────────────────────────────────────────
    "experience_summary": (
        "Insurance and reinsurance operations professional with 10+ years owning end-to-end "
        "operational processes in MGA, broker and programme environments. Proven track record "
        "managing BPO supplier relationships, drafting SOPs, monitoring KPIs/KRIs/SLAs, and "
        "acting as primary operational point of contact for managing agents and external partners. "
        "Targeting EU-wide remote, Barcelona hybrid, and selected European relocation roles in "
        "insurance operations, Business Analysis, digital transformation, Guidewire/platform change, "
        "AI automation consulting and AI governance. Digital transformation practitioner: BPMN process "
        "design, gap analysis, requirements definition, stakeholder alignment across operations and IT. "
        "AI governance exposure: EU AI Act + DORA Art. 28 compliance tooling, risk assessment and "
        "third-party vendor onboarding."
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
        "business_analysis_transformation": [
            "Requirements definition",
            "Process mapping",
            "Gap analysis",
            "BPMN process design",
            "Stakeholder management",
            "UAT coordination",
            "Operating model implementation",
            "Digital transformation support",
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
            "DORA Art. 28 vendor governance",
            "EU AI Act governance concepts",
            "Regulatory frameworks",
        ],
        "data_technology": [
            "SQL (intermediate)",
            "Python (intermediate)",
            "Power BI",
            "Snowflake",
            "Guidewire",
            "Jira",
            "UAT",
            "MS Office & Google Workspace",
        ],
        "ai_automation_stack": [
            "Claude API & Claude.ai",
            "Prompt engineering",
            "RAG concepts",
            "LangGraph workflow orchestration",
            "CrewAI system design",
            "MCP (Model Context Protocol)",
            "n8n workflow automation",
            "GitHub Actions automation",
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
                "Own end-to-end ops for managing agent partners across UK and Europe",
                "BPO supplier trainer and referral point, SLA monitoring",
                "SOP drafting and standardisation across platform processes",
                "KPI/KRI/SLA monitoring for internal and external performance",
                "Tech supplier collaboration: UAT lead, deliverable sign-off",
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
                "French market operations coordination",
                "Primary contact for French-speaking partners",
                "Process documentation and regulatory compliance across French book",
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
                "Authority compliance, SLA performance and documentation standards",
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
                "Coordinated 17 international programmes",
                "SOPs, governance and compliance controls (OFAC, HM Treasury, SDN)",
                "Primary interface: fronting insurers, reinsurers, managing agents and regulators",
            ],
        },
        {
            "title": "Corporate Insurance Advisor & Operations",
            "company": "Riskmedia Insurance Brokers",
            "type": "Broker",
            "period": "2019–2021",
            "location": "Barcelona",
            "highlights": ["End-to-end operations for corporate client portfolio"],
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
        {"title": "3 years Dentistry", "institution": "Universidad Europea de Madrid", "year": ""},
    ],

    # ── Scoring Keywords ─────────────────────────────────────────
    "keywords_high_priority": [
        "insurance operations", "underwriting operations", "claims operations", "claims transformation",
        "reinsurance operations", "MGA", "managing general agent", "delegated underwriting", "DUA",
        "Lloyd's", "coverholder", "programme", "program", "bordereaux",
        "Guidewire", "PolicyCenter", "ClaimCenter", "Duck Creek", "FINEOS",
        "BPO", "SOP", "KPI", "SLA", "process improvement", "Solvency II", "DORA",
        "business analyst", "business analysis", "process analyst", "requirements", "BPMN",
        "digital transformation", "implementation consultant", "functional consultant", "product owner",
        "AI consultant", "AI automation", "AI implementation", "intelligent automation",
        "workflow automation", "process automation", "AI governance", "responsible AI", "EU AI Act",
        "Claude API", "LLM", "generative AI", "LangGraph", "CrewAI", "MCP", "n8n",
    ],

    "keywords_medium_priority": [
        "insurance", "reinsurance", "broker", "underwriting", "claims", "fintech",
        "data operations", "process excellence", "operational excellence",
        "remote", "EU", "Europe", "EMEA", "Barcelona", "Spain", "relocation",
        "SQL", "Power BI", "Snowflake", "Python", "Jira", "agile", "continuous improvement",
        "AI", "automation", "workflow", "API", "integration", "data pipeline", "GitHub Actions",
    ],

    "keywords_exclude": [
        "junior", "graduate", "intern", "entry level", "apprentice",
        "sales development representative", "sdr", "account executive", "pure sales",
        "pure software engineer", "pure frontend", "pure backend", "pure devops",
        "data scientist (pure ML)", "research scientist", "actuary", "actuarial",
        "insurance agent", "life insurance agent", "field adjuster",
    ],

    "min_match_score": 50,

    # ── CV Summaries for AI generation ───────────────────────────
    "cv_summary_en": (
        "Insurance and reinsurance operations professional with 10+ years across MGA, broker, carrier "
        "and programme environments. Combines senior insurance operations experience with Business "
        "Analysis, digital transformation and AI-enabled automation skills, including process mapping, "
        "requirements definition, UAT, Guidewire exposure, SQL, Power BI, Claude API, LangGraph, CrewAI, "
        "MCP and n8n. Targeting EU-wide remote, Barcelona hybrid and selected European relocation roles "
        "in insurance operations, BA/consulting and AI automation."
    ),

    "cv_summary_es": (
        "Profesional de operaciones de seguros y reaseguros con 10+ años en entornos MGA, corredores, "
        "aseguradoras y programas internacionales. Combina experiencia senior en operaciones de seguros "
        "con Business Analysis, transformación digital y automatización con IA: process mapping, requisitos, "
        "UAT, Guidewire, SQL, Power BI, Claude API, LangGraph, CrewAI, MCP y n8n. Busca roles remotos en "
        "Europa, híbridos en Barcelona o relocación europea selectiva para BA/consulting y AI automation."
    ),
}
