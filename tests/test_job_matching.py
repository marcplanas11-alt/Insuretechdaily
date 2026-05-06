"""Test the updated job matching logic."""
from job_hunter import is_insurance_relevant, is_eu_eligible

# Test cases for is_insurance_relevant: (text, expected_result)
relevance_cases = [
    # Traditional insurance (should match)
    ("Operations Manager at Lloyd's coverholder in Madrid", True),
    ("Insurance Operations Specialist - MGA", True),

    # AI + Finance/Insurance (should match - new scope)
    ("AI Product Engineer - Claims automation with Claude API", True),
    ("LangGraph workflow orchestration for insurance underwriting", True),
    ("AI Implementation Specialist - Treasury Operations FinTech", True),

    # AI Engineer + insurance domain (should match - new AI engineering scope)
    ("AI Engineer building automation for insurance claims processing", True),
    ("Machine learning engineer for insurance underwriting platform", True),
    ("LLM Engineer at InsurTech startup, finance automation focus", True),

    # BA + insurance/fintech domain (should match)
    ("Business Analyst at MGA, process documentation and SOP ownership", True),
    ("Digital transformation business analyst at fintech scale-up", True),

    # AI without domain context (should NOT match)
    ("Senior Software Engineer - Python/Go SaaS product", False),
    ("ML Engineer for Computer Vision startup in Berlin", False),

    # Finance/Ops but no insurance (should NOT match)
    ("Financial Operations Manager - FAANG", False),

    # Mixed: has domain words but not insurance-specific
    ("Workflow automation engineer for business processes", False),
    ("Process automation with Python and APIs", False),
]

# Test cases for is_eu_eligible: (location, description, expected_eligible)
eligibility_cases = [
    ("Remote", "", True),
    ("Remote EU", "", True),
    ("Barcelona, Spain", "", True),
    ("London, UK", "", True),
    ("Remote (US)", "", False),
    ("United States only", "", False),
    ("San Francisco, CA", "", False),
    ("Remote", "must be authorized to work in the us", False),
    ("", "remote emea, work from anywhere in europe", True),
    ("New York, NY", "", False),
]

print("Testing is_insurance_relevant() logic:\n")
passed = failed = 0
for text, expected in relevance_cases:
    result = is_insurance_relevant(text)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    if result == expected:
        passed += 1
    else:
        failed += 1
    print(f"{status}: '{text[:65]}' => {result} (expected {expected})")

print(f"\n{passed}/{len(relevance_cases)} relevance tests passed")

print("\nTesting is_eu_eligible() logic:\n")
eu_passed = eu_failed = 0
for loc, desc, expected in eligibility_cases:
    eligible, reason = is_eu_eligible(loc, desc)
    result = eligible
    status = "✅ PASS" if result == expected else "❌ FAIL"
    if result == expected:
        eu_passed += 1
    else:
        eu_failed += 1
    print(f"{status}: loc='{loc}' desc='{desc[:40]}' => {result} [{reason}] (expected {expected})")

print(f"\n{eu_passed}/{len(eligibility_cases)} eligibility tests passed")
total = passed + eu_passed
total_all = len(relevance_cases) + len(eligibility_cases)
print(f"\n{'='*50}")
print(f"TOTAL: {total}/{total_all} tests passed")
if failed + eu_failed > 0:
    exit(1)
