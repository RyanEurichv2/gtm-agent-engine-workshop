import copy
import importlib
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class FakeTool:
    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def invoke(self, input_data):
        return self.function(**input_data)


def install_import_stubs():
    package = types.ModuleType("gtm_agent")
    package.__path__ = [str(ROOT)]
    sys.modules["gtm_agent"] = package

    langsmith = types.ModuleType("langsmith")
    langsmith.traceable = lambda **kwargs: (lambda function: function)
    sys.modules["langsmith"] = langsmith

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda **kwargs: None
    sys.modules["dotenv"] = dotenv

    pydantic = types.ModuleType("pydantic")

    class BaseModel:
        def model_dump(self):
            return self.__dict__

    pydantic.BaseModel = BaseModel
    sys.modules["pydantic"] = pydantic

    langchain = types.ModuleType("langchain")
    tools = types.ModuleType("langchain.tools")
    tools.tool = lambda function: FakeTool(function)
    tools.ToolRuntime = type("ToolRuntime", (), {})
    langchain.tools = tools
    sys.modules["langchain"] = langchain
    sys.modules["langchain.tools"] = tools

    langchain_openai = types.ModuleType("langchain_openai")

    class ChatOpenAI:
        def __init__(self, **kwargs):
            pass

        def with_structured_output(self, model):
            return self

    langchain_openai.ChatOpenAI = ChatOpenAI
    sys.modules["langchain_openai"] = langchain_openai

    deepagents = types.ModuleType("deepagents")
    deepagents.create_deep_agent = lambda **kwargs: None
    sys.modules["deepagents"] = deepagents


install_import_stubs()
data_service = importlib.import_module("gtm_agent.data_service")
gtm_agent = importlib.import_module("gtm_agent.gtm_agent")


class ProspectUpdateTest(unittest.TestCase):
    def test_update_rebuild_and_score_include_new_technology(self):
        prospect_id = "LEAD-90001"
        offering_id = "OFFER-10007"
        original_record = copy.deepcopy(data_service.PROSPECTS[prospect_id])
        data_service._PROFILES.clear()

        try:
            profile_before = gtm_agent.build_prospect_profile.invoke(
                {"prospect_id": prospect_id}
            )["prospect_profile"]
            self.assertNotIn("Okta", profile_before["tech_stack"])

            updated = gtm_agent.update_prospect_info.invoke(
                {"prospect_id": prospect_id, "technology": "Okta"}
            )
            self.assertTrue(updated["updated"])

            profile_after = gtm_agent.build_prospect_profile.invoke(
                {"prospect_id": prospect_id}
            )["prospect_profile"]
            self.assertIn("Okta", profile_after["tech_stack"])

            offering = gtm_agent.lookup_offering.invoke(
                {"offering_id": offering_id}
            )["offering"]

            class FakeResult:
                def model_dump(self):
                    return {
                        "score": 100.0,
                        "justification": "The prospect has Okta.",
                    }

            class FakeScorer:
                def invoke(self, messages):
                    self.prospect_text = messages[1]["content"]
                    return FakeResult()

            scorer = FakeScorer()
            gtm_agent._scoring_llm = scorer
            result = gtm_agent.score_prospect.invoke(
                {"prospect_profile": profile_after, "offering": offering}
            )

            self.assertIn("Okta", scorer.prospect_text)
            self.assertIn("Okta", result["justification"])
        finally:
            data_service.PROSPECTS[prospect_id] = original_record
            data_service._PROFILES.clear()


if __name__ == "__main__":
    unittest.main()
