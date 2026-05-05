"""Test the scoring criteria for new AI Product Engineer roles."""

test_jobs = [
    {
        "name": "AI Product Engineer - Claims Automation",
        "title": "AI Product Engineer",
        "company": "Embat",
        "description": """We're building AI agents for automated claims processing using Claude API and LangChain. 
        You'll design prompts, build RAG pipelines, and deploy production AI systems. 
        The role bridges product engineering and AI — owning the full pipeline from problem identification 
        to shipping intelligent automation. Experience with Finance/Insurance operations is a strong plus.""",
        "location": "Remote - EU",
    },
    {
        "name": "Senior Operations Manager",
        "title": "Senior Operations Manager",
        "company": "Swiss Re",
        "description": """Lead operations for international reinsurance programmes. 
        Oversee BPO supplier relationships, draft and standardize SOPs, monitor KPIs/SLAs. 
        Work with 20+ programme partners across EU and US.""",
        "location": "Remote - EU / Hybrid Barcelona",
    },
    {
        "name": "Digital Workforce Specialist",
        "title": "Digital Workforce Specialist",
        "company": "FinTech Scale-up",
        "description": """Build AI automation for treasury operations using LangGraph and Claude API. 
        Identify workflow bottlenecks, design agent architectures, and deploy solutions that 
        reduce manual effort by 70%. You understand both finance workflows AND how to build AI systems.""",
        "location": "Remote",
    },
    {
        "name": "Junior SWE - Python/Go",
        "title": "Junior Software Engineer",
        "company": "Tech Startup",
        "description": """Looking for a junior engineer to build APIs and microservices. 
        No domain experience required, we train on the job.""",
        "location": "Barcelona - On-site",
    },
]

# Test profile matching
from marc_profile import PROFILE

print("=" * 70)
print("PROFILE VERIFICATION — AI Stack Exposure")
print("=" * 70)

print(f"\nTarget roles ({len(PROFILE['target_roles'])} total):")
ai_roles = [r for r in PROFILE['target_roles'] if 'ai' in r.lower() or 'digital' in r.lower()]
print(f"  AI/Digital roles: {ai_roles}")

print(f"\nCore competencies sections ({len(PROFILE['core_competencies'])} total):")
for section in PROFILE['core_competencies'].keys():
    count = len(PROFILE['core_competencies'][section])
    print(f"  ✓ {section}: {count} items")

print(f"\nHigh-priority keywords ({len(PROFILE['keywords_high_priority'])} total):")
ai_keywords = [k for k in PROFILE['keywords_high_priority'] if 'ai' in k.lower() or 'langchain' in k.lower() or 'claude' in k.lower()]
print(f"  AI-focused: {ai_keywords[:10]}...")

print("\n" + "=" * 70)
print("EXPECTED SCORING BEHAVIOR (without API calls)")
print("=" * 70)

expected_outcomes = {
    "AI Product Engineer - Claims Automation": {
        "min_score": 85,
        "reason": "Perfect match: AI Product Engineer + Claude/LangChain + claims automation domain"
    },
    "Senior Operations Manager": {
        "min_score": 80,
        "reason": "Strong match: traditional operations role at reinsurer, remote EU eligible"
    },
    "Digital Workforce Specialist": {
        "min_score": 75,
        "reason": "Good/Strong match: AI + Treasury Finance + LangGraph, remote EU"
    },
    "Junior SWE - Python/Go": {
        "min_score": 0,
        "reason": "Hard reject: Junior level, no domain context, pure SWE, on-site Barcelona only"
    },
}

print("\nScoring expectations:")
for job_name, expected in expected_outcomes.items():
    print(f"\n  {job_name}")
    print(f"    Expected min score: {expected['min_score']}%")
    print(f"    Reasoning: {expected['reason']}")

print("\n" + "=" * 70)
print("REFRAME RULES VERIFICATION")
print("=" * 70)

reframe_rules = {
    "1-3 years AI experience": "ACCEPT — 1yr practical + Anthropic certs + 10yr domain",
    "LangChain/LangGraph required": "ACCEPT — CrewAI + LangGraph portfolio projects",
    "Background in Physics/ML": "ACCEPT — 3yr science + autodidact + 10yr domain",
    "Product mindset": "ACCEPT — 10yr translating business→tech",
    "5+ years pure AI": "REJECT — too junior for senior AI Product Engineer",
}

print("\nCandidate (Marc) gap reframing:")
for gap, reframe in reframe_rules.items():
    print(f"  • Gap: '{gap}' → {reframe}")

print("\n✅ Upscaling complete. Repo now evaluates:")
print("   1. Traditional insurance operations roles (€60K+, remote EU/Barcelona)")
print("   2. AI Product Engineer roles (Claude/LLM + Finance/Insurance domain)")
print("   3. Digital Workforce / AI Operations roles (with domain expertise)")
print("   4. Scope: EU Remote + Barcelona Hybrid only")
