"""Test the updated job matching logic."""
from job_hunter import is_insurance_relevant

# Test cases: (text, expected_result)
test_cases = [
    # Traditional insurance (should match)
    ("Operations Manager at Lloyd's coverholder in Madrid", True),
    ("Insurance Operations Specialist - MGA", True),
    
    # AI + Finance/Insurance (should match - new scope)
    ("AI Product Engineer - Claims automation with Claude API", True),
    ("LangGraph workflow orchestration for insurance underwriting", True),
    ("AI Implementation Specialist - Treasury Operations FinTech", True),
    
    # AI without domain context (should NOT match)
    ("Senior Software Engineer - Python/Go SaaS product", False),
    ("ML Engineer for Computer Vision startup in Berlin", False),
    
    # Finance/Ops but no insurance (should NOT match with strict "insurance" requirement)
    ("Financial Operations Manager - FAANG", False),
    
    # Mixed: has domain words but not insurance-specific (could be marginal)
    ("Workflow automation engineer for business processes", False),
    ("Process automation with Python and APIs", False),
]

print("Testing is_insurance_relevant() logic:\n")
passed = 0
failed = 0

for text, expected in test_cases:
    result = is_insurance_relevant(text)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    if result == expected:
        passed += 1
    else:
        failed += 1
    print(f"{status}: '{text[:60]}...' => {result} (expected {expected})")

print(f"\n{passed}/{len(test_cases)} tests passed")
