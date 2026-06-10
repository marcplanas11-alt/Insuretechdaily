# Company & Job Opportunity Schema

## Objective
Standardize company and opportunity ingestion across InsurTech Daily.

---

# Company Schema

```json
{
  "company_name": "",
  "company_domain": "",
  "industry": "InsurTech",
  "subcategory": "Embedded Insurance",
  "headquarters": "",
  "regions_hiring": ["Europe", "UK", "EMEA"],
  "remote_policy": "Remote",
  "relocation_support": true,
  "visa_sponsorship": true,
  "english_required": true,
  "ats_provider": "Greenhouse",
  "careers_url": "",
  "linkedin_url": "",
  "active_hiring": true,
  "source": "LinkedIn",
  "priority_score": 0,
  "notes": ""
}
```

---

# Job Schema

```json
{
  "job_title": "",
  "department": "Engineering",
  "seniority": "Mid",
  "employment_type": "Full-time",
  "location": "Remote Europe",
  "salary_range": "",
  "remote": true,
  "hybrid": false,
  "relocation_support": true,
  "visa_sponsorship": true,
  "english_speaking": true,
  "region": "EMEA",
  "job_url": "",
  "published_at": "",
  "ats_provider": "Lever",
  "source": "Otta"
}
```

---

# Recommended Enumerations

## Industries
- InsurTech
- FinTech
- HealthTech
- HRTech
- ClimateTech
- Cybersecurity
- AI Infrastructure

## ATS Providers
- Greenhouse
- Lever
- Ashby
- Workable
- SmartRecruiters
- Teamtailor
- BambooHR

## Remote Policies
- Remote
- Hybrid
- Onsite

## Regions
- Europe
- UK
- EMEA
- Africa
- Remote Europe
- Remote EMEA
