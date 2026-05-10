"""
Tests for is_insurance_relevant() covering all three tracks.
Track A: insurance/reinsurance/MGA domain.
Track B: BA/digital transformation + financial/regulated context.
Track C: AI orchestration tools + finance-insurance domain.
"""
import pytest
from job_hunter import is_insurance_relevant


class TestTrackAMatching:
    """Traditional insurance/reinsurance domain — must match."""

    def test_lloyds_coverholder(self):
        assert is_insurance_relevant("Operations Manager at Lloyd's coverholder in London")

    def test_mga_operations(self):
        assert is_insurance_relevant("Insurance Operations Specialist — MGA platform remote")

    def test_reinsurance_analyst(self):
        assert is_insurance_relevant("Senior reinsurance analyst EMEA remote")

    def test_underwriting_operations(self):
        assert is_insurance_relevant("Underwriting operations manager remote EU")

    def test_bordereaux_manager(self):
        assert is_insurance_relevant("Bordereaux data quality manager insurance")

    def test_delegated_authority(self):
        assert is_insurance_relevant("Delegated underwriting authority operations specialist")

    def test_solvency_ii(self):
        assert is_insurance_relevant("Solvency II compliance manager insurance group")

    def test_insurtech(self):
        assert is_insurance_relevant("Operations lead at fast-growing insurtech startup")

    def test_fintech_financial_services(self):
        assert is_insurance_relevant("Operations analyst at fintech financial services platform")

    def test_claims_processing(self):
        assert is_insurance_relevant("Claims processing manager insurance company remote")


class TestTrackBMatching:
    """BA/Digital Transformation + financial/regulated domain — must match."""

    def test_ba_insurtech(self):
        assert is_insurance_relevant("AI Product Owner Insurance Claims Automation insurtech")

    def test_ba_financial_services(self):
        assert is_insurance_relevant("Business analyst financial services digital transformation remote")

    def test_digital_transformation_insurance(self):
        assert is_insurance_relevant("Digital transformation analyst insurance operations remote")

    def test_requirements_fintech(self):
        assert is_insurance_relevant("Requirements elicitation analyst fintech payments remote")

    def test_bpmn_insurance(self):
        assert is_insurance_relevant("BPMN process mapping analyst insurance company")

    def test_gap_analysis_financial(self):
        assert is_insurance_relevant("Gap analysis consultant financial services regulatory compliance")

    def test_process_analyst_insurance(self):
        assert is_insurance_relevant("Process analyst insurance digital transformation BPMN")

    def test_ba_regulatory(self):
        assert is_insurance_relevant("Business analyst regulatory compliance banking fintech remote")


class TestTrackCMatching:
    """AI Product Engineer + finance/insurance domain context — must match."""

    def test_ai_product_engineer_claims(self):
        assert is_insurance_relevant("AI Product Engineer claims automation with Claude API")

    def test_langgraph_insurance(self):
        assert is_insurance_relevant("LangGraph workflow orchestration for insurance underwriting")

    def test_ai_implementation_treasury(self):
        assert is_insurance_relevant("AI Implementation Specialist treasury operations fintech")

    def test_crewai_reinsurance(self):
        assert is_insurance_relevant("CrewAI multi-agent developer reinsurance contract review")

    def test_mcp_bordereaux(self):
        assert is_insurance_relevant("MCP orchestration engineer bordereaux intake automation")

    def test_digital_workforce_finance(self):
        assert is_insurance_relevant("Digital workforce specialist AI agent finance operations")

    def test_llm_insurance_automation(self):
        assert is_insurance_relevant("LLM engineer insurance claims triage automation remote")

    def test_rag_financial_services(self):
        assert is_insurance_relevant("RAG pipeline developer financial services compliance")

    def test_ai_agent_insurance(self):
        assert is_insurance_relevant("AI agent engineer insurance platform automation remote")


class TestHardExcludes:
    """Roles that must NOT be matched by any track."""

    def test_pure_software_engineer(self):
        assert not is_insurance_relevant("Senior Software Engineer Python Go SaaS product")

    def test_ml_research_computer_vision(self):
        assert not is_insurance_relevant("ML Engineer computer vision NLP deep learning startup")

    def test_pure_frontend(self):
        assert not is_insurance_relevant("Frontend developer React TypeScript UI components")

    def test_ai_no_domain_context(self):
        assert not is_insurance_relevant("AI engineer LLM RAG generic SaaS platform no domain")

    def test_generic_ba_no_domain(self):
        assert not is_insurance_relevant("Business analyst IT project management no domain")

    def test_game_developer(self):
        assert not is_insurance_relevant("Game developer Unity C# 3D engine graphics")

    def test_generic_process_automation(self):
        assert not is_insurance_relevant("Workflow automation engineer business processes general")

    def test_generic_python_api(self):
        assert not is_insurance_relevant("Python developer API microservices no domain")

    def test_financial_ops_faang_no_insurance(self):
        # Generic "financial operations" without insurance/fintech specifics should not match
        # NOTE: this is a marginal case — test documents expected behaviour
        result = is_insurance_relevant("Financial Operations Manager FAANG tech company")
        # "financial" alone is not enough without a regulated-domain qualifier — should be False
        assert result is False
