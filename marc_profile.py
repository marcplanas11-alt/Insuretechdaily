"""
Marc Planas Callico — Professional Profile v5.0
Source of truth for job_hunter.py scoring and CV generation.
Triple Track: Insurance Ops/AI (A) · BA/Digital Transformation (B) · AI Product Engineer (C)
New Track D: AI Consultant/Lead/Architect (EU-focused AI platforms)
"""

PROFILE = {
    "name": "Marc Planas Callico",
    "email": "marcplanas11@gmail.com",
    "linkedin": "linkedin.com/in/intlinsure",
    "github": "github.com/intlinsure",
    "location": "Barcelona · CET · Remote-ready EMEA",

    # ── Languages ────────────────────────────────────────────────
    "languages": [
        {"lang": "Spanish",  "level": "Native"},
        {"lang": "Catalan",  "level": "Native"},
        {"lang": "English",  "level": "C2"},
        {"lang": "French",   "level": "C1"},
        {"lang": "Italian",  "level": "B2"},
    ],

    # ── Location & Work Preferences ──────────────────────────────
    "location_preferences": {
        "remote_eu": True,
        "hybrid_barcelona": True,
        "hybrid_madrid": False,      # HARD BLOCKER
        "onsite_only": False,
        "outside_eu": False,
    },

    # ── Salary ───────────────────────────────────────────────────
    "min_salary_eur": 60000,
    "target_salary_eur_ab": 75000,   # Track A/B target
    "target_salary_eur_c": 65000,    # Track C early-stage target
    "target_salary_eur_d": 85000,    # Track D (Lead/Architect) — more senior
    "salary_note": (
        "Floor €60K absolute. Target €75K+ Track A/B, €65K+ Track C early-stage, €85K+ Track D Lead/Architect. "
        "Roles without salary info still considered."
    ),

    # ── Triple Track Positioning ─────────────────────────────────
    "tracks": {
        "A": {
            "name": "Insurance Ops / AI Transformation",
            "headline": (
                "AI-Enabled Insurance Operations · MGA · Lloyd's · Delegated Authority "
                "· CrewAI · LangGraph · English C2 · French C1"
            ),
            "target_companies": [
                "MGA operators", "Lloyd's market", "Swiss Re", "Synpulse",
                "reinsurance platforms", "Head of Insurance Ops EMEA", "insurtechs with ops team",
            ],
            "threshold": 6.0,
        },
        "B": {
            "name": "Digital Transformation BA / Consultant",
            "headline": (
                "Digital Transformation Analyst · AI-Enabled Process Design "
                "· Insurance & Financial Services · Remote CET · English C2 · French C1"
            ),
            "target_companies": [
                "Allianz in-house digital team", "Big 4 insurance practice",
                "boutique consulting insurance-adjacent", "CoverGo BA/product side",
                "insurtechs with product ops or transformation role",
            ],
            "threshold": 6.0,
        },
        "C": {
            "name": "AI Product Engineer / Digital Workforce",
            "headline": (
                "AI Product Engineer · Insurance & FinTech Domain · CrewAI · LangGraph "
                "· Claude API · MCP · Python · English C2 · French C1"
            ),
            "target_companies": [
                "Insurtechs and scale-ups with AI Product Engineer role",
                "AI Implementation Specialist opportunities",
                "companies building agents for financial/insurance workflows",
                "startups valuing hacker mindset + domain expertise + demonstrable AI stack",
            ],
            "threshold": 5.5,   # Lower: emergent profile, JDs often over-spec
        },
        "D": {
            "name": "AI Consultant / Lead / Architect (EU Platforms)",
            "headline": (
                "AI Consultant / Technical Lead · AI Agent Architecture · Claude/LLM Expertise "
                "· Insurance/FinTech Domain · Remote EU/Barcelona · English C2 · French C1"
            ),
            "target_companies": [
                "Anthropic Enterprise Consulting Partners (EU)",
                "AI implementation consultancies (insurance/finance focus)",
                "LangChain/LlamaIndex ecosystem companies",
                "AI-native platforms expanding EU insurance market",
                "Prompt engineering & AI architecture specialists",
            ],
            "threshold": 6.5,   # Higher: leadership position, expect strong match
        },
    },

    # ── Target Roles ─────────────────────────────────────────────
    "target_roles": [
        # Track A — Insurance Ops / AI Transformation
        "Operations Manager",
        "Insurance Operations Manager",
        "Head of Insurance Operations",
        "Head of Operations EMEA",
        "Underwriting Operations Specialist",
        "Underwriting Operations Manager",
        "Reinsurance Operations Specialist",
        "MGA Operations Manager",
        "Programme Operations Manager",
        "Data Operations Manager",
        "BPO Manager",
        "Process Excellence Manager",
        # Track B — BA / Digital Transformation
        "Business Analyst",
        "Business Analyst (InsurTech)",
        "Business Analyst (FinTech)",
        "AI Business Analyst",
        "Digital Transformation Business Analyst",
        "Digital Transformation Analyst",
        "Process Analyst",
        "Operational Business Analyst",
        "Senior Business Analyst",
        # Track C — AI Product Engineer / Digital Workforce
        "AI Product Engineer",
        "AI Implementation Specialist",
        "Digital Workforce Specialist",
        "AI Operations Specialist",
        "AI-powered Operations Manager",
        "Automation Engineer (Finance/Insurance)",
        # Track D — AI Consultant / Lead / Architect
        "AI Consultant (Enterprise)",
        "AI Solutions Architect",
        "Technical Lead — AI/LLM",
        "AI Systems Architect",
        "Prompt Engineering Lead",
        "Head of AI Implementation",
        "AI Technical Director",
        "Principal AI Engineer",
        "Lead AI/ML Engineer",
    ],

    # ── GitHub Projects (verified public portfolio) ───────────────
    "github_projects": [
        {
            "name": "reinsurance-contract-crew",
            "stack": "CrewAI · Claude API · FileReadTool",
            "status": "public",
            "bullet_a": (
                "Three-agent CrewAI system for automated reinsurance contract review — "
                "30+ data points extracted, Lloyd's standard benchmarked, DORA-aligned "
                "reports with structured audit trail. Estimated 80%+ reduction in manual review time."
            ),
            "bullet_b": (
                "Process redesign and AI automation of reinsurance contract review: requirements "
                "elicitation, BPMN mapping, three-agent CrewAI implementation, Lloyd's platform "
                "benchmarking, DORA-aligned reporting."
            ),
        },
        {
            "name": "claims-triage-langgraph",
            "stack": "LangGraph · Claude API · ChromaDB · RAG · Streamlit · Pytest",
            "status": "public",
            "bullet_a": (
                "LangGraph state machine for claims triage — Claude API reasoning, conditional "
                "routing, human review node, DORA Art. 28 audit trail, Pytest CI, Streamlit interface."
            ),
            "bullet_b": (
                "End-to-end digital transformation of claims triage: BPMN AS-IS/TO-BE, LangGraph "
                "state machine, human-in-the-loop design, gap analysis, Streamlit operational "
                "interface, DORA Art. 28 audit trail."
            ),
        },
        {
            "name": "insurance-ai-governance-pack",
            "stack": "Python · EU AI Act · DORA Art. 28 · gap analysis",
            "status": "public",
            "bullet_a": (
                "EU AI Act (Arts. 6–9, 10, 11, 13) risk assessments and DORA Art. 28 third-party "
                "risk documentation for AI vendor onboarding in MGA/reinsurance context — gap "
                "analysis templates and human-in-the-loop design patterns."
            ),
        },
        {
            "name": "sql-insurance-data-quality",
            "stack": "SQL · CTEs · window functions · synthetic data",
            "status": "public",
            "bullet_a": (
                "SQL (intermediate) query library for insurance data quality: CTEs, window "
                "functions, anomaly detection, bordereaux KPI tracking."
            ),
        },
        {
            "name": "bordereaux-intake-n8n-mcp",
            "stack": "n8n · MCP · Claude API · webhook · email",
            "status": "public",
            "bullet_a": (
                "n8n + MCP orchestration workflow for automated bordereaux intake validation — "
                "AI schema checking, error flagging, QC reporting as MCP endpoint."
            ),
        },
        {
            "name": "ba-process-models",
            "stack": "BPMN 2.0 · draw.io",
            "status": "public",
            "bullet_b": (
                "BPMN 2.0 process models for insurance claims triage and bordereaux intake — "
                "AS-IS / TO-BE with business case documentation."
            ),
        },
        {
            "name": "agent-evaluation-dashboard",
            "stack": "Streamlit · Python · multi-agent metrics · DORA",
            "status": "public",
            "bullet_a": (
                "Streamlit evaluation dashboard monitoring AI agent performance: accuracy, latency, "
                "Human-in-the-loop trigger rate, DORA Art. 28 compliance status per deployed agent."
            ),
        },
        {
            "name": "Insuretechdaily",
            "stack": "GitHub Actions · market intelligence",
            "status": "production",
            "bullet_a": (
                "GitHub Actions-powered market intelligence pipeline monitoring MGA/insurtech "
                "market activity in real time."
            ),
        },
    ],

    # ── Career History (verified, rules-compliant) ────────────────
    "career_history": [
        {
            "title": "Operations Data Manager",
            "company": "Accelerant",
            "type": "MGA Reinsurance Platform",
            "period": "Apr 2025–Present",
            "location": "Barcelona / Remote",
            # RULE: UK and Europe ONLY — never US
            "highlights": [
                "Own end-to-end operational processes for 20+ managing agent partners across UK and Europe",
                "BPO supplier trainer and referral point; SLA/KPI/KRI monitoring and escalation",
                "SOP drafting and standardisation across all platform processes",
                "Tech supplier collaboration (Intrali): UAT lead for Gen2 platform, DORA compliance sign-off",
                "SQL, Power BI, Snowflake for business cases; Claude API and GitHub Actions for automation",
                "Designed and deployed Python automation pipeline (Insuretechdaily) for MGA market intelligence",
            ],
        },
        {
            "title": "Insurance Program Manager — French Market",
            "company": "Sompo International",
            "type": "Insurer",
            "period": "Apr 2024–Mar 2025",
            "location": "Barcelona / Paris",
            # RULE: Correct title; Guidewire CRM, 3 countries, delegated authority
            "highlights": [
                "Managed French market insurance programme operations end-to-end across 3 countries",
                "Primary contact for French-speaking partners; stakeholder management 20+ parties",
                "Guidewire CRM expansion ownership: process documentation, UAT, go-live coordination",
                "Delegated authority monitoring, regulatory compliance, French book governance",
            ],
        },
        {
            "title": "International Programs Operations Specialist",
            "company": "Zurich Insurance Group",
            "type": "Global Insurer",
            "period": "Feb 2023–Mar 2024",
            "location": "Barcelona",
            # RULE: Property/BI, 30+ international programmes — NOT generic
            "highlights": [
                "Governance and compliance for 30+ international Commercial Lines programmes (Property/BI)",
                "Authority compliance monitoring, SLA performance management, documentation standards",
                "Training on complex, non-standard scenarios; cross-border regulatory coordination",
                "OFAC, HM Treasury, SDN sanctions screening; Solvency II operational controls",
            ],
        },
        {
            "title": "International Programs Manager",
            "company": "Confide",
            "type": "Reinsurance Broker",
            "period": "Oct 2021–Jan 2023",
            "location": "Barcelona",
            # RULE: "coordinated and managed 17 EXISTING programmes" — NEVER "created from scratch"
            "highlights": [
                "Coordinated and managed 17 existing international reinsurance programmes across EMEA",
                "SOPs, governance frameworks and compliance controls (OFAC, HM Treasury, SDN)",
                "Primary interface: fronting insurers, reinsurers, managing agents, and regulators",
                "Bordereaux reconciliation, delegated authority oversight, reporting to capacity providers",
            ],
        },
        {
            "title": "Underwriter — Media & Entertainment",
            "company": "Riskmedia",
            "type": "Insurance Broker (Delegated Authority)",
            "period": "Dec 2019–Sep 2021",
            "location": "Barcelona",
            # RULE: Delegated Authority, CRM Seg Elevia (NOT Salesforce)
            "highlights": [
                "Underwriting under delegated authority for Media & Entertainment book",
                "CRM Seg Elevia administration and portfolio data management",
                "End-to-end policy lifecycle: submission, binding, endorsement, renewal",
            ],
        },
        {
            "title": "Underwriter — Personal Lines & Leisure",
            "company": "Liberty Seguros",
            "type": "Insurer",
            "period": "Aug 2016–Nov 2019",
            "location": "Barcelona",
            # RULE: Full underwriting authority, coaching, both awards
            "highlights": [
                "Full underwriting authority for Personal Lines and Leisure product portfolio",
                "Coaching junior underwriters; referral point for complex cases",
                "Best Efficiency Idea award for CRM workflow redesign",
                "Best Telephone Resolution Q1 2019",
            ],
        },
        {
            "title": "Insurance Operations",
            "company": "SegurCaixa Adeslas",
            "type": "Insurer (Bancassurance)",
            "period": "Mar 2015–Jul 2016",
            "location": "Barcelona",
            # RULE: Claims refusal assessment
            "highlights": [
                "Claims refusal assessment and operational management in bancassurance distribution",
            ],
        },
    ],

    # ── Education & Certifications ────────────────────────────────
    # RULES: PSM I = NEVER included. Only Anthropic Skilljar + ICEA = verifiable certifications.
    # All courses labelled [course], NOT certification.
    "education": [
        # Verifiable certifications (badge/credential)
        {"title": "Corredor de Seguros Grupo B",
         "institution": "ICEA", "year": "2022", "type": "certification"},
        {"title": "Building with the Claude API",
         "institution": "Anthropic Skilljar", "year": "2025", "type": "certification"},
        {"title": "AI Fluency: Framework & Foundations + Capabilities",
         "institution": "Anthropic Skilljar", "year": "2025", "type": "certification"},

        # Courses completed (label as [course])
        {"title": "Prompt Engineering CoT/few-shot/XML [course]",
         "institution": "Great Learning + Anthropic", "year": "2025", "type": "course"},
        {"title": "SQL Window Functions/CTEs/Quality [course]",
         "institution": "Mode Analytics", "year": "2025", "type": "course"},
        {"title": "Multi-Agent AI Systems with CrewAI [course]",
         "institution": "DeepLearning.AI", "year": "2026", "type": "course"},
        {"title": "AI Agents with LangGraph [course]",
         "institution": "DeepLearning.AI", "year": "2026", "type": "course"},
        {"title": "Agentic RAG with LlamaIndex [course]",
         "institution": "Hugging Face", "year": "2026", "type": "course"},
        {"title": "EU AI Act + DORA Governance [course]",
         "institution": "IBM SkillsBuild / EUR-Lex", "year": "2026", "type": "course"},
        {"title": "BPMN 2.0 Process Modelling [course]",
         "institution": "bpmn.io / draw.io", "year": "2026", "type": "course"},
        {"title": "BABOK Core Techniques [course]",
         "institution": "IIBA / Adaptive US", "year": "2026", "type": "course"},
        {"title": "Lean Six Sigma Yellow Belt [course]",
         "institution": "Six Sigma Council", "year": "2026", "type": "course"},
        {"title": "MECE Frameworks McKinsey/BCG [course]",
         "institution": "Victor Cheng", "year": "2026", "type": "course"},
        {"title": "Google AI Essentials [course]",
         "institution": "Google / Coursera", "year": "2026", "type": "course"},
        {"title": "Agile Project Management [course]",
         "institution": "Google / Coursera", "year": "2026", "type": "course"},

        # In progress
        {"title": "Evaluating and Debugging Generative AI [in progress]",
         "institution": "DeepLearning.AI", "year": "2026", "type": "in_progress"},
        {"title": "A2A Agent2Agent Protocol [in progress]",
         "institution": "DeepLearning.AI", "year": "2026", "type": "in_progress"},
        {"title": "Long-Term Agentic Memory LangGraph [in progress]",
         "institution": "DeepLearning.AI", "year": "2026", "type": "in_progress"},

        # Academic background
        {"title": "3 years of Dentistry — Universidad Europea de Madrid",
         "institution": "Universidad Europea de Madrid", "year": "N/A", "type": "academic"},
    ],

    # ── Core Competencies ─────────────────────────────────────────
    "core_competencies": {
        "operations_process": [
            "End-to-end process ownership",
            "SOP drafting & standardisation",
            "BPO oversight & SLA/KPI/KRI monitoring",
            "Continuous improvement & process automation identification",
            "BAU management",
            "Submission process management",
            "Account clearance & set-up",
            "Workflow optimisation",
        ],
        "managing_agent_support": [
            "Operating model implementation",
            "Portfolio analysis",
            "Delegated underwriting authority monitoring",
            "Operational controls & governance",
            "Stakeholder guidance (20+ managing agents)",
            "Coverholder & bordereaux standards",
        ],
        "ba_transformation": [
            "Requirements elicitation & user stories",
            "BPMN 2.0 process modelling (AS-IS/TO-BE)",
            "Gap analysis frameworks (AI governance, process improvement)",
            "Stakeholder management & workshops",
            "BABOK core techniques",
            "MECE frameworks (McKinsey/BCG)",
            "Lean Six Sigma Yellow Belt [course]",
            "Agile BA & backlog management",
        ],
        "compliance_governance": [
            "EU AI Act Arts. 4, 6–9, 10, 11, 13 (applied insurance context)",
            "DORA Art. 28 (ICT third-party risk, AI vendor onboarding)",
            "Solvency II",
            "IFRS 17",
            "Sanctions screening (OFAC, HM Treasury, SDN)",
            "Good Local Standards",
            "Human-in-the-loop design (regulated workflows)",
            "Audit trail design (DORA Art. 28, AI explainability)",
        ],
        "ai_automation_stack": [
            # Production (Accelerant + public portfolio)
            "Python intermediate (pandas, openpyxl, requests, GitHub Actions)",
            "SQL intermediate (CTEs, window functions, data quality, bordereaux KPIs)",
            "Claude API (Anthropic Skilljar certified: RAG, tool use, agents, MCP, PDF processing)",
            "CrewAI (3-agent reinsurance contract review, production portfolio)",
            "LangGraph (state machine claims triage, RAG/ChromaDB, HITL, DORA Art. 28)",
            "MCP (Model Context Protocol) — bordereaux-intake-n8n-mcp",
            "n8n workflow orchestration",
            "Streamlit (operational interfaces, evaluation dashboards)",
            "Pytest + CI (test suites AI operational systems)",
            "GitHub Actions automation pipelines",
            # In progress / completing
            "LlamaIndex / FAISS (HF course completed, portfolio in progress)",
            "A2A Agent2Agent Protocol (DeepLearning.AI in progress)",
        ],
        "ai_consulting_leadership": [
            "Claude API expert (production use, prompt optimization, cost reduction)",
            "LLM architecture & multi-agent system design",
            "RAG pipeline design for regulated sectors (insurance, finance)",
            "AI governance frameworks (EU AI Act, DORA compliance)",
            "Technical team leadership & mentoring",
            "AI vendor evaluation & onboarding (DORA Art. 28)",
            "ROI modeling for AI automation projects",
        ],
        "data_bi": [
            "Power BI",
            "Snowflake",
            "Guidewire CRM",
            "Salesforce CRM",
            "Jira",
            "ChatGPT API",
        ],
    },

    # ── Hard Blockers (Phase 1) ───────────────────────────────────
    "hard_blockers": [
        "madrid presencial",
        "madrid on-site",
        "on-site madrid",
        "salary below 55000",
        "phd required",
        "phd in ai",
        "phd in ml",
        "open-source contributions to ai frameworks required",
        "ai research scientist",
        "model training",
        "fine-tuning required",
        "ntt data",
        "junior level",
        "graduate role",
        "intern",
    ],

    # ── Track Identification Keywords ─────────────────────────────
    "track_keywords": {
        "A": [
            "mga", "managing general agent", "lloyd's", "delegated authority",
            "bordereaux", "coverholder", "reinsurance operations",
            "insurance platform", "binding authority",
            "solvency ii", "dora", "ifrs 17",
        ],
        "B": [
            "business analyst", "digital transformation", "requirements",
            "stakeholder", "process improvement", "bpmn", "agile ba",
            "gap analysis", "consulting", "change management",
            "requirements elicitation", "user stories", "process mapping",
        ],
        "C": [
            "ai product engineer", "ai implementation", "llm", "agent",
            "workflow automation", "claude", "gpt", "langchain", "langgraph",
            "mcp", "hacker mindset", "ship fast", "digital workforce",
            "friction removal", "internal tooling", "crewai", "rag",
        ],
        "D": [
            "ai consultant", "technical lead", "ai architect", "solutions architect",
            "prompt engineer lead", "head of ai", "principal engineer",
            "ai systems", "claude expert", "llm architect",
            "ai governance", "ai implementation lead",
        ],
    },

    # ── ATS Scoring Keywords ──────────────────────────────────────
    "keywords_high_priority": [
        # Track A — Insurance Ops
        "insurance operations", "underwriting operations", "reinsurance operations",
        "MGA", "managing general agent", "delegated underwriting", "DUA",
        "Lloyd's", "coverholder", "programme", "program", "bordereaux",
        "BPO", "SOP", "KPI", "SLA", "process improvement",
        "Solvency II", "DORA", "EU AI Act", "sanctions", "OFAC", "compliance",
        "operations manager", "operations specialist", "operations analyst",
        "insurtech", "insurance platform",
        # Track B — BA / Digital Transformation
        "business analyst", "business analysis", "process analyst",
        "digital transformation", "operational analyst",
        "requirements elicitation", "BPMN", "gap analysis", "user stories",
        "stakeholder management", "process mapping",
        # Track C — AI Product Engineer
        "AI product engineer", "AI implementation", "digital workforce",
        "AI automation", "workflow automation", "process automation",
        "Claude API", "LLM", "large language model", "generative AI",
        "LangChain", "LangGraph", "CrewAI", "agent", "orchestration",
        "prompt engineering", "RAG", "retrieval augmented",
        "AI-powered", "AI-enabled", "automated workflow",
        "MCP", "n8n", "human-in-the-loop",
        "finance operations AI", "insurance automation", "claims automation",
        # Track D — AI Consultant / Lead / Architect
        "AI consultant", "AI architect", "technical lead", "solutions architect",
        "AI solutions", "prompt engineering lead", "head of AI",
        "principal engineer", "AI governance", "Claude expert",
        "AI systems architect", "AI implementation lead", "Chief AI Officer",
    ],

    "keywords_medium_priority": [
        "insurance", "reinsurance", "broker", "underwriting",
        "data operations", "process excellence", "operational excellence",
        "remote", "EU", "Europe", "Barcelona", "CET",
        "SQL", "Power BI", "Snowflake", "Python",
        "agile", "scrum", "lean six sigma", "continuous improvement",
        "AI", "automation", "workflow",
        "API", "integration", "data pipeline",
        "GitHub Actions", "CI/CD",
        "fintech", "finance automation", "financial services",
        "Streamlit", "Pytest", "LlamaIndex",
    ],

    "keywords_exclude": [
        "junior", "graduate", "intern", "entry level", "apprentice",
        "pure software engineer", "pure frontend", "pure backend", "pure devops",
        "data scientist pure ml", "research scientist",
        "actuary", "actuarial", "pricing analyst",
        "sales agent", "insurance agent", "life insurance agent",
        "claims adjuster", "field adjuster",
        "phd required", "model training", "fine-tuning",
    ],

    "min_match_score": 50,

    # ── CV Summaries ──────────────────────────────────────────────
    "cv_summary_en": (
        "AI-enabled insurance operations professional with 10+ years building complex workflows "
        "in MGA, reinsurance and broker environments — MGA/Lloyd's, delegated authority, bordereaux, "
        "DORA Art. 28, EU AI Act. Now architect and deploy AI agents (Claude API, LangGraph, CrewAI) "
        "to automate the same processes managed manually for a decade. Anthropic-certified; fluent in "
        "prompt engineering, RAG, multi-agent systems and MCP. Bilingual English C2 / Spanish native; "
        "French C1, Italian B2."
    ),

    "cv_summary_es": (
        "Profesional de operaciones de seguros con 10+ años diseñando procesos complejos en entornos "
        "MGA, reaseguros y corredores — Lloyd's, delegated authority, bordereaux, DORA Art. 28, EU AI Act. "
        "Ahora construyo y despliego agentes AI (Claude API, LangGraph, CrewAI) para automatizar los mismos "
        "procesos gestionados manualmente durante una década. Certificado Anthropic; experto en prompt "
        "engineering, RAG, sistemas multi-agente y MCP. Bilingüe inglés C2 / español nativo; francés C1, "
        "italiano B2."
    ),

    # ── Market Data (for scoring context) ────────────────────────
    "market_data": {
        "uk_it_vacancies_insurance_growth": "+27.7% Q1 2025",
        "ai_hiring_insurance_global": "+16% Q2 2024",
        "digital_transformation_roles_europe": "+25-35% YoY",
        "agentic_ai_deployments_insurance": "1/5 deployments Q4 2025",
        "uk_ai_skills_gap": "97% UK companies with gap (57% technical)",
    },

    # ── Pipeline (current active applications) ───────────────────
    "active_pipeline": [
        {"company": "Synpulse London", "role": "Manager Reinsurance CRID",
         "stage": "Round 3/4", "probability": "55-65%"},
    ],
}
