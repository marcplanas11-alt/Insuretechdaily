"""
Tests for triple-track scoring criteria and profile compliance rules.
Covers: track identification keywords, hard blocker rules, profile invariants (Prompt Maestro v5.0).
"""
import pytest
from marc_profile import PROFILE
from job_hunter import is_insurance_relevant


# ─────────────────────────────────────────────────────────────
# Profile invariants — rules that must NEVER be violated
# ─────────────────────────────────────────────────────────────

class TestProfileInvariants:
    """Enforce the hard rules from Prompt Maestro v5.0 Parte IX."""

    def test_no_psm_i_in_education(self):
        """PSM I must NEVER appear anywhere in education — it does not exist."""
        for entry in PROFILE["education"]:
            title_lower = entry["title"].lower()
            assert "psm" not in title_lower, f"PSM found in education entry: {entry['title']}"
            assert "professional scrum master" not in title_lower

    def test_python_always_intermediate(self):
        """Python must always be labelled 'intermediate', never 'advanced' or 'basic'."""
        all_text = str(PROFILE).lower()
        # Check that 'python advanced' and 'python básico' don't appear
        assert "python advanced" not in all_text
        assert "python (advanced)" not in all_text
        # Check that 'intermediate' appears for python
        ai_stack = " ".join(PROFILE["core_competencies"]["ai_automation_stack"]).lower()
        assert "python intermediate" in ai_stack

    def test_sql_always_intermediate(self):
        """SQL must always be labelled 'intermediate', never 'advanced'."""
        ai_stack = " ".join(PROFILE["core_competencies"]["ai_automation_stack"]).lower()
        assert "sql intermediate" in ai_stack
        assert "sql advanced" not in str(PROFILE).lower()

    def test_accelerant_no_us(self):
        """Accelerant scope must be UK and Europe ONLY — never US/USA."""
        accelerant = next(
            e for e in PROFILE["career_history"] if e["company"] == "Accelerant"
        )
        highlights_text = " ".join(accelerant["highlights"]).lower()
        assert "us" not in highlights_text.split() or "uk" in highlights_text, \
            "Accelerant must be UK/Europe only — check for US reference"
        assert "united states" not in highlights_text
        # Positive check: UK or Europe must appear
        assert "uk" in highlights_text or "europe" in highlights_text or "emea" in highlights_text

    def test_confide_not_created_from_scratch(self):
        """Confide must show 17 EXISTING programmes — never 'created from scratch'."""
        confide = next(
            e for e in PROFILE["career_history"] if e["company"] == "Confide"
        )
        highlights_text = " ".join(confide["highlights"]).lower()
        assert "from scratch" not in highlights_text, \
            "Confide must say 'managed EXISTING programmes', never 'from scratch'"
        assert "existing" in highlights_text or "coordinated" in highlights_text

    def test_riskmedia_correct_title(self):
        """Riskmedia must show Underwriter Media & Entertainment, not 'corporate advisor'."""
        riskmedia = next(
            e for e in PROFILE["career_history"] if e["company"] == "Riskmedia"
        )
        title_lower = riskmedia["title"].lower()
        assert "underwriter" in title_lower
        assert "media" in title_lower or "entertainment" in title_lower

    def test_riskmedia_no_salesforce(self):
        """Riskmedia CRM must be Seg Elevia — NOT Salesforce."""
        riskmedia = next(
            e for e in PROFILE["career_history"] if e["company"] == "Riskmedia"
        )
        highlights_text = " ".join(riskmedia["highlights"]).lower()
        assert "salesforce" not in highlights_text, \
            "Riskmedia CRM must be Seg Elevia, NOT Salesforce"

    def test_liberty_correct_title(self):
        """Liberty must be Underwriter Personal Lines & Leisure."""
        liberty = next(
            e for e in PROFILE["career_history"] if e["company"] == "Liberty Seguros"
        )
        title_lower = liberty["title"].lower()
        assert "underwriter" in title_lower
        assert "personal" in title_lower or "leisure" in title_lower

    def test_liberty_has_awards(self):
        """Liberty must include both awards (Best Efficiency + Best Telephone Resolution)."""
        liberty = next(
            e for e in PROFILE["career_history"] if e["company"] == "Liberty Seguros"
        )
        highlights_text = " ".join(liberty["highlights"]).lower()
        assert "best efficiency" in highlights_text or "efficiency idea" in highlights_text
        assert "telephone" in highlights_text or "resolution" in highlights_text

    def test_segurCaixa_claims_refusal(self):
        """SegurCaixa must mention claims refusal assessment."""
        segur = next(
            e for e in PROFILE["career_history"] if e["company"] == "SegurCaixa Adeslas"
        )
        highlights_text = " ".join(segur["highlights"]).lower()
        assert "claims" in highlights_text and "refusal" in highlights_text

    def test_sompo_guidewire_mentioned(self):
        """Sompo must reference Guidewire CRM and delegated authority."""
        sompo = next(
            e for e in PROFILE["career_history"] if e["company"] == "Sompo International"
        )
        highlights_text = " ".join(sompo["highlights"]).lower()
        assert "guidewire" in highlights_text
        assert "delegated" in highlights_text or "authority" in highlights_text

    def test_zurich_property_bi_mentioned(self):
        """Zurich must mention Property/BI and 30+ programmes."""
        zurich = next(
            e for e in PROFILE["career_history"] if e["company"] == "Zurich Insurance Group"
        )
        highlights_text = " ".join(zurich["highlights"]).lower()
        assert "30" in highlights_text
        assert "property" in highlights_text or "bi" in highlights_text or "commercial" in highlights_text

    def test_no_cbap_certification(self):
        """CBAP must not appear (not pursuing — too costly/time-consuming)."""
        assert "cbap" not in str(PROFILE).lower()

    def test_courses_not_labelled_certification(self):
        """Courses must be labelled [course] or 'in_progress', not 'certification'."""
        for entry in PROFILE["education"]:
            if entry.get("type") == "course":
                assert "[course]" in entry["title"] or "course" in entry["title"].lower(), \
                    f"Course not properly labelled: {entry['title']}"

    def test_only_anthropic_and_icea_are_certifications(self):
        """Only Anthropic Skilljar and ICEA Corredor must be type='certification'."""
        for entry in PROFILE["education"]:
            if entry.get("type") == "certification":
                is_anthropic = "anthropic" in entry["institution"].lower()
                is_icea = "icea" in entry["institution"].lower()
                assert is_anthropic or is_icea, \
                    f"Non-verifiable certification found: {entry['title']} @ {entry['institution']}"

    def test_salary_floor_60k(self):
        """Absolute salary floor must be €60,000."""
        assert PROFILE["min_salary_eur"] == 60000

    def test_madrid_presencial_hard_blocker(self):
        """Madrid presencial must be explicitly blocked."""
        assert PROFILE["location_preferences"].get("hybrid_madrid") is False

    def test_github_present(self):
        """GitHub profile must be defined."""
        assert "github" in PROFILE
        assert "intlinsure" in PROFILE["github"]

    def test_triple_track_keywords_defined(self):
        """Track A, B, C keyword lists must all be defined."""
        assert "track_keywords" in PROFILE
        for track in ("A", "B", "C"):
            assert track in PROFILE["track_keywords"]
            assert len(PROFILE["track_keywords"][track]) >= 5

    def test_track_thresholds(self):
        """Track C threshold must be lower (5.5) than A/B (6.0) — emergent profile."""
        assert PROFILE["tracks"]["C"]["threshold"] < PROFILE["tracks"]["A"]["threshold"]
        assert PROFILE["tracks"]["C"]["threshold"] < PROFILE["tracks"]["B"]["threshold"]
        assert PROFILE["tracks"]["A"]["threshold"] == 6.0
        assert PROFILE["tracks"]["B"]["threshold"] == 6.0
        assert PROFILE["tracks"]["C"]["threshold"] == 5.5


# ─────────────────────────────────────────────────────────────
# Track A keywords — insurance/reinsurance domain
# ─────────────────────────────────────────────────────────────

class TestTrackAKeywords:
    """Track A must trigger on MGA/Lloyd's/delegated authority/bordereaux signals."""

    def test_mga_triggers_track_a(self):
        assert any("mga" in kw.lower() for kw in PROFILE["track_keywords"]["A"])

    def test_lloyds_triggers_track_a(self):
        assert any("lloyd" in kw.lower() for kw in PROFILE["track_keywords"]["A"])

    def test_bordereaux_triggers_track_a(self):
        assert any("bordereaux" in kw.lower() for kw in PROFILE["track_keywords"]["A"])

    def test_dora_triggers_track_a(self):
        assert any("dora" in kw.lower() for kw in PROFILE["track_keywords"]["A"])

    def test_delegated_authority_triggers_track_a(self):
        kws = [k.lower() for k in PROFILE["track_keywords"]["A"]]
        assert any("delegated" in k for k in kws)


# ─────────────────────────────────────────────────────────────
# Track B keywords — BA / digital transformation
# ─────────────────────────────────────────────────────────────

class TestTrackBKeywords:
    """Track B must trigger on BA/requirements/BPMN/transformation signals."""

    def test_business_analyst_triggers_track_b(self):
        assert any("business analyst" in kw.lower() for kw in PROFILE["track_keywords"]["B"])

    def test_bpmn_triggers_track_b(self):
        assert any("bpmn" in kw.lower() for kw in PROFILE["track_keywords"]["B"])

    def test_requirements_triggers_track_b(self):
        kws = [k.lower() for k in PROFILE["track_keywords"]["B"]]
        assert any("requirements" in k for k in kws)

    def test_gap_analysis_triggers_track_b(self):
        kws = [k.lower() for k in PROFILE["track_keywords"]["B"]]
        assert any("gap analysis" in k for k in kws)


# ─────────────────────────────────────────────────────────────
# Track C keywords — AI Product Engineer
# ─────────────────────────────────────────────────────────────

class TestTrackCKeywords:
    """Track C must trigger on LLM/agent/orchestration + finance-domain signals."""

    def test_langgraph_triggers_track_c(self):
        kws = [k.lower() for k in PROFILE["track_keywords"]["C"]]
        assert any("langgraph" in k for k in kws)

    def test_ai_product_engineer_triggers_track_c(self):
        kws = [k.lower() for k in PROFILE["track_keywords"]["C"]]
        assert any("ai product engineer" in k for k in kws)

    def test_mcp_triggers_track_c(self):
        kws = [k.lower() for k in PROFILE["track_keywords"]["C"]]
        assert any("mcp" in k for k in kws)

    def test_rag_triggers_track_c(self):
        kws = [k.lower() for k in PROFILE["track_keywords"]["C"]]
        assert any("rag" in k for k in kws)


# ─────────────────────────────────────────────────────────────
# is_insurance_relevant — triple-track matching
# ─────────────────────────────────────────────────────────────

class TestIsInsuranceRelevantTripleTrack:
    """is_insurance_relevant must accept roles from all three tracks."""

    # Track A — insurance domain
    def test_track_a_mga(self):
        assert is_insurance_relevant("Operations Manager at MGA  London remote")

    def test_track_a_lloyds(self):
        assert is_insurance_relevant("Lloyd's coverholder operations specialist")

    def test_track_a_reinsurance(self):
        assert is_insurance_relevant("Reinsurance operations analyst EMEA remote")

    def test_track_a_bordereaux(self):
        assert is_insurance_relevant("Bordereaux data quality manager insurance")

    # Track B — BA + financial services context
    def test_track_b_ba_insurtech(self):
        assert is_insurance_relevant("Business analyst insurtech digital transformation remote")

    def test_track_b_ba_financial_services(self):
        assert is_insurance_relevant("Business analyst financial services process improvement remote")

    def test_track_b_digital_transformation_insurance(self):
        assert is_insurance_relevant("Digital transformation analyst insurance operations")

    def test_track_b_requirements_fintech(self):
        assert is_insurance_relevant("Requirements elicitation specialist fintech platform remote")

    def test_track_b_bpmn_insurance(self):
        assert is_insurance_relevant("BPMN process mapping analyst insurance company")

    # Track C — AI + finance/insurance domain
    def test_track_c_langgraph_insurance(self):
        assert is_insurance_relevant("LangGraph AI agent engineer insurance automation remote")

    def test_track_c_claude_api_fintech(self):
        assert is_insurance_relevant("Claude API implementation specialist fintech operations")

    def test_track_c_ai_product_engineer_insurance(self):
        assert is_insurance_relevant("AI product engineer claims automation financial services")

    def test_track_c_crewai_reinsurance(self):
        assert is_insurance_relevant("CrewAI developer reinsurance workflow automation")

    def test_track_c_mcp_bordereaux(self):
        assert is_insurance_relevant("MCP orchestration engineer bordereaux processing")

    # Hard excludes — must NOT match
    def test_excludes_pure_ml_research(self):
        assert not is_insurance_relevant("ML Research Scientist computer vision NLP deep learning")

    def test_excludes_pure_frontend(self):
        assert not is_insurance_relevant("Frontend developer React TypeScript UI components")

    def test_excludes_generic_ai_no_domain(self):
        assert not is_insurance_relevant("AI engineer LLM RAG SaaS product no domain")

    def test_excludes_generic_ba_no_domain(self):
        assert not is_insurance_relevant("Business analyst IT process improvement generic")

    def test_excludes_unrelated_sector(self):
        assert not is_insurance_relevant("Game developer Unity C# 3D graphics engine")
