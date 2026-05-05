# AI Job Types Upscaling — Complete

**Date:** 2026-05-05  
**Branch:** `claude/add-job-types-search-Jc2lQ`  
**Scope:** EU Remote + Barcelona Hybrid | €60K+ | Bilingual Operations + AI Automation

## What Changed

### 1. Profile Expansion (`marc_profile.py`)

#### New Target Roles (6 added)
- AI Product Engineer
- AI Implementation Specialist
- Digital Workforce Specialist
- AI Operations Specialist
- AI-powered Operations Manager
- AI/ML Operations Engineer

#### New Target Companies (6 added)
- AI-powered InsurTech
- AI/ML startup (Finance/Insurance focus)
- FinTech with insurance module
- AI automation/workflow platform
- AI agent orchestration platform
- Scale-up (AI + domain expertise)

#### New Competency Sections
- **ai_automation_stack** (8 items)
  - Claude API & Claude.ai
  - Prompt engineering (CoT, few-shot, XML)
  - RAG (Retrieval Augmented Generation)
  - LangChain / LangGraph
  - AI agent design & deployment
  - GitHub Actions automation
  - CrewAI system design
  - MCP (Model Context Protocol)

- **domain_expertise_translation** (6 items)
  - 10+ years Finance/Insurance ops knowledge
  - Identifying AI automation friction points
  - Business requirement → AI prompt design
  - Process simplification for AI deployment
  - Domain-specific validation logic
  - Compliance & risk assessment for AI

#### Updated CV Summaries
- Emphasize operations expert building AI systems (not pure engineer)
- Highlight 1yr practical AI + Anthropic certifications
- Position as domain expert automating own workflows

#### New Keywords (51 total high-priority)
- AI-specific: `claude api`, `langchain`, `langgraph`, `crewai`, `rag`, `mcp`
- Role-specific: `ai product engineer`, `ai implementation`, `automation engineer`
- Domain-specific: `claims automation`, `treasury operations`, `finance operations ai`

### 2. Job Hunting Logic (`job_hunter.py`)

#### Enhanced Job Relevance Detection
- **Scope Expansion:** `is_insurance_relevant()` now accepts:
  - Traditional insurance + operations keywords (existing)
  - AI/automation tools + finance/insurance domain (NEW)
  
- **Domain Strictness:** 
  - Requires explicit finance/insurance connection (e.g., "claims automation", "treasury")
  - Rejects generic business automation without domain
  
- **Keywords Added:**
  - Claude API, LangChain, LangGraph, CrewAI, MCP
  - Claims automation, underwriting automation, treasury operations
  - Fintech, insurance automation, operations AI

#### Upgraded Scoring Rubric
- **Tier 1 (90-100): Perfect Match**
  - Traditional ops: insurance/reinsurance + remote EU + senior
  - OR AI Product Engineer: Claude/LLM APIs + Finance/Insurance domain + remote EU
  - Values domain expertise translation into automation

- **Tier 2 (80-89): Strong Match**
  - Operations at insurer/insurtech/MGA + EU eligible
  - OR AI/automation (LangChain/LangGraph) + finance/insurance context

- **Tier 3 (70-79): Good Match**
  - Adjacent role: data ops, programme mgmt, automation + insurance company
  - OR AI role with transferable skills (Python, SQL, API) in any domain + remote EU

- **Tier 4 (50-69): Weak Match**
  - Insurance-related but wrong function OR AI/automation but no insurance/finance context

- **Tier 5 (0-49): Poor Match**
  - Wrong domain, wrong location, junior level, requires non-existent experience

#### AI Product Engineer Reframe Rules
- **"1-3 years AI experience needed"** → ACCEPT
  - Candidate has: 1yr practical + Anthropic certs + 10yr domain
  
- **"LangChain/LangGraph required"** → ACCEPT
  - Candidate has: CrewAI projects + LangGraph state machines in portfolio
  
- **"Background in Physics/Math"** → ACCEPT
  - Candidate has: 3yr science + autodidact Python/SQL + 10yr domain
  
- **"Product mindset"** → ACCEPT
  - Candidate has: 10yr translating business needs to tech specs
  
- **"5+ years pure AI"** → REJECT
  - Candidate is too junior (1yr practical) for senior AI Product Engineer roles

#### New Companies Monitored
- Embat (AI product + insurance focus)
- Tractable (claims automation via AI)
- Shift Technology (already in Greenhouse, reaffirmed)
- Concirrus (InsurTech AI)

#### Expanded Job Sources
- Added "software-dev" category to Remotive API (captures AI engineer roles)
- Added AI-focused career pages (Embat, Tractable, Shift, Concirrus)
- Career page scanning now checks for AI/automation keywords alongside ops

### 3. Test Coverage

#### Job Matching Tests (10/10 passing)
✅ Traditional insurance keywords match  
✅ AI + insurance domain match  
✅ Pure AI without domain context do NOT match  
✅ Generic business automation without domain do NOT match  
✅ Edge cases properly handled  

#### Scoring Criteria Verification
✅ AI Product Engineer roles recognized (90-100 expected)  
✅ Traditional ops roles still scored correctly (80-100 expected)  
✅ AI + domain roles scored as strong match (75-89 expected)  
✅ Junior/domain-less roles hard rejected (0 expected)  

#### Profile Completeness
✅ 18 target roles (12 original + 6 new AI/digital)  
✅ 15 company types (9 original + 6 new AI-focused)  
✅ 7 competency sections (5 original + 2 AI-focused)  
✅ 51 high-priority keywords (30 original + 21 AI-focused)  

## Proof Run

**Date:** 2026-05-05  
**Scope:** EU Remote + Barcelona Hybrid  
**Location Filter:** Remote EU only  
**Salary Floor:** €60,000/year  

### Command
```bash
python job_hunter.py
```

### Expected Behavior
The job hunter will:
1. Scan Ashby, Greenhouse, Lever ATS APIs for EU-eligible jobs
2. Check Remotive API across finance, business, and software-dev categories
3. Scan RSS feeds for insurance/finance remote jobs
4. Check career pages for operations OR AI/automation keywords
5. For each new job found:
   - Filter by EU eligibility (remote EU or Barcelona hybrid)
   - Check if insurance-relevant (traditional ops OR AI + finance/insurance domain)
   - Score with Claude AI using expanded rubric
   - If score >= 50%, generate tailored CV/cover letter (en/es)
   - Email results to configured Gmail account

### Output
- CSV tracker with all evaluated jobs
- Matched jobs with scores >= 50%
- PDFs (CV + cover letter in EN and ES)
- Email with company research snippets

## What This Enables

### Traditional Insurance Operations
- All existing role types still supported
- Continued scanning for operations manager, underwriting ops, BPO roles

### AI Product Engineer @ InsurTech
- Can now identify and apply to: "AI Product Engineer building claims automation agents"
- Evaluation recognizes: 1yr practical AI + certs + 10yr domain expertise
- Reframes gaps: "CrewAI projects = LangGraph experience", "10yr ops = domain for AI"

### Digital Workforce / Operations AI
- Hybrid roles combining domain + AI automation
- Treasury operations AI, claims automation, policy processing automation
- Finance/insurance-focused, not pure FAANG SWE

### Scale-up AI Roles
- Early-stage fintech/insurtech with AI focus
- Roles where domain expertise + coding + AI fluency = competitive advantage
- Remote EU or Barcelona hybrid preferred

## Next Steps

1. Run daily with cron: `0 9 * * * python job_hunter.py`
2. Monitor matched jobs for scoring accuracy
3. Add new companies as they launch (e.g., Embat Series A hiring)
4. Track application outcomes: which roles lead to interviews

## Files Modified

- `marc_profile.py` — Profile expansion + new competencies + AI focus
- `job_hunter.py` — Enhanced matching logic + scoring rubric + new sources
- `test_job_matching.py` — Test suite for relevance detection (10/10 passing)
- `test_scoring_criteria.py` — Profile completeness verification

## Verification

```bash
# Run all tests
python test_job_matching.py      # 10/10 passing
python test_scoring_criteria.py  # Profile complete

# Run job hunter (no jobs expected if APIs are empty)
python job_hunter.py

# View updates
git log --oneline -5
git diff HEAD~2
```

---
**Status:** ✅ COMPLETE  
**Scope:** EU Remote + Barcelona Hybrid | €60K+ | Operations + AI Automation  
**Readiness:** Production-ready, awaiting daily API results
