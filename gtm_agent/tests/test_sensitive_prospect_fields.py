import json
import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

from gtm_agent import gtm_agent


SENSITIVE_FIELDS = {
    "billing_qualification",
    "tax_id",
    "date_of_birth",
    "card_on_file",
    "credit_check_ref",
}


def _keys(payload):
    if isinstance(payload, dict):
        return set(payload).union(*(_keys(value) for value in payload.values()))
    if isinstance(payload, list):
        return set().union(*(_keys(value) for value in payload))
    return set()


def test_prospect_tool_payloads_exclude_sensitive_fields():
    prospect = gtm_agent.get_prospect.invoke({"prospect_id": "LEAD-12853"})
    profile = gtm_agent.build_prospect_profile.invoke({"prospect_id": "LEAD-39002"})

    payloads = [prospect, profile]
    assert not SENSITIVE_FIELDS.intersection(_keys(payloads))
    assert not SENSITIVE_FIELDS.intersection(_keys(json.loads(json.dumps(payloads))))
