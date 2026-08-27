import os
from types import SimpleNamespace

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent.gtm_agent import send_prospect_email


def test_disqualified_prospect_is_blocked_without_sending(monkeypatch):
    prospect = {
        "prospect_id": "LEAD-50004",
        "name": "Aiden Park",
        "email": "aiden.park@cedargrovelogistics.com",
    }
    uuid_calls = []
    monkeypatch.setattr(
        "gtm_agent.gtm_agent.uuid.uuid4",
        lambda: uuid_calls.append(True),
    )

    result = send_prospect_email.func(
        prospect,
        "Availability",
        "Are you available?",
        SimpleNamespace(config={}),
        from_rep={"name": "Tara Kim", "email": "tara.kim@northpoint.com"},
    )

    assert result == {"status": "blocked", "reason": "prospect is disqualified"}
    assert uuid_calls == []


def test_qualified_prospect_is_sent():
    prospect = {
        "prospect_id": "LEAD-12853",
        "name": "Omar Okafor",
        "email": "omar.okafor@lakesideanalytics.com",
    }

    result = send_prospect_email.func(
        prospect,
        "Availability",
        "Are you available?",
        SimpleNamespace(config={}),
        from_rep={"name": "Tara Kim", "email": "tara.kim@northpoint.com"},
    )

    assert result["status"] == "sent"
    assert result["to"] == prospect["email"]
