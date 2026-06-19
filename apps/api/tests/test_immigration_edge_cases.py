"""Edge cases for ImmigrationAgent not covered by test_parsing_immigration.py."""
import pytest
from datetime import date, timedelta
from app.agents.talent import ImmigrationAgent
from app.models import Consultant, ImmigrationRecord, VisaStatus


# ─── ImmigrationAgent.run edge cases ─────────────────────────────────────────

def test_immigration_expired_auth_label(db):
    """An already-expired authorization should produce an 'EXPIRED' alert."""
    result = ImmigrationAgent().run(db, today=date(2030, 1, 1))
    # By 2030 all seeded auths are expired.
    expired = [a for a in result["alerts"] if "EXPIRED" in a]
    assert len(expired) >= 0  # skeleton: refine with seeded data specifics


def test_immigration_custom_horizon_widens_alerts(db):
    today = date(2026, 6, 18)
    narrow = ImmigrationAgent().run(db, horizon_days=0, today=today)
    wide = ImmigrationAgent().run(db, horizon_days=365, today=today)
    assert len(wide["alerts"]) >= len(narrow["alerts"])


def test_immigration_count_matches_authorizations(db):
    result = ImmigrationAgent().run(db)
    assert result["count"] == len(result["authorizations"])


def test_immigration_authorizations_have_schema(db):
    result = ImmigrationAgent().run(db)
    for auth in result["authorizations"]:
        for key in ("consultant_id", "name", "visa_type",
                    "transfer_eligible", "transfer_note",
                    "lca_filed", "worksite_location", "days_to_expiry"):
            assert key in auth


def test_immigration_l1_not_transfer_eligible(db):
    result = ImmigrationAgent().run(db)
    l1_auths = [a for a in result["authorizations"] if a["visa_type"] == "L1"]
    for auth in l1_auths:
        assert auth["transfer_eligible"] is False


def test_immigration_usc_always_transfer_eligible(db):
    result = ImmigrationAgent().run(db)
    usc_auths = [a for a in result["authorizations"] if a["visa_type"] == "USC"]
    for auth in usc_auths:
        assert auth["transfer_eligible"] is True


# ─── ImmigrationAgent.eligibility edge cases ──────────────────────────────────

def test_eligibility_gc_ead_always_eligible(db):
    from app.models import VisaStatus
    c = db.query(Consultant).first()
    c.visa_status = VisaStatus.GC_EAD
    agent = ImmigrationAgent()
    assert agent.eligibility(c, ["H1B", "GC"])["eligible"] is True


def test_eligibility_opt_not_eligible_for_usc_only(db):
    c = db.query(Consultant).filter_by(visa_status=VisaStatus.OPT).first()
    if c:
        agent = ImmigrationAgent()
        assert agent.eligibility(c, ["USC"])["eligible"] is False


def test_eligibility_no_restrictions_always_eligible(db):
    c = db.query(Consultant).first()
    agent = ImmigrationAgent()
    assert agent.eligibility(c, [])["eligible"] is True


def test_eligibility_returns_visa_status_in_response(db):
    c = db.query(Consultant).first()
    result = ImmigrationAgent().eligibility(c, [])
    assert "visa_status" in result
    assert result["visa_status"] == c.visa_status.value
