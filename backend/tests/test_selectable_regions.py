"""Company switcher / bill company list = Admin's ticks + the ERP home company (always)."""
import os

for _k in ("READER_DB_SERVER", "READER_DB_NAME", "READER_DB_USER", "READER_DB_PASSWORD"):
    os.environ.setdefault(_k, "test")

import json  # noqa: E402

import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from api import routes_auth  # noqa: E402
from auth.security import CurrentUser, selectable_regions_for  # noqa: E402
from database.models import (  # noqa: E402
    Base,
    ErpAuthExpenseUsers,
    ErpExpenseMultiRegionUserRegion,
    ErpExpenseRegionConfig,
    ErpMasterExpenseRole,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    role = ErpMasterExpenseRole(role_code="employee", role_name="Employee")
    session.add(role)
    matrix = json.dumps({"stages": ["accountant"]})
    regions = {
        code: ErpExpenseRegionConfig(region_code=code, region_name=code, approval_matrix_json=matrix)
        for code in ("DUBAI", "UAE", "KSA", "OMAN")
    }
    session.add_all(regions.values())
    session.flush()
    session.info["role"] = role
    session.info["regions"] = regions
    yield session
    session.close()


def _person(db, name, ticks=()):
    u = ErpAuthExpenseUsers(user_name=name, display_name=name, password_hash="x",
                            role_id=db.info["role"].role_id)
    db.add(u)
    db.flush()
    for code in ticks:
        db.add(ErpExpenseMultiRegionUserRegion(
            user_id=u.user_id, region_id=db.info["regions"][code].region_id, is_active=1))
    db.commit()
    return u


def _sign_in(db, monkeypatch, user, home):
    monkeypatch.setattr(routes_auth, "authenticate_user", lambda _db, _u, _p: user)
    monkeypatch.setattr(routes_auth, "resolve_default_region_code", lambda _db, _id: home)
    out = routes_auth.login(routes_auth.LoginRequest(username=user.user_name, password="x"), db)
    return out.user


def test_ticked_home_is_listed_once(db):
    priya = _person(db, "priya", ticks=("DUBAI", "KSA"))
    assert sorted(selectable_regions_for(db, priya, "DUBAI")) == ["DUBAI", "KSA"]


def test_home_moved_in_erp_is_added(db, monkeypatch):
    """Ravi was ticked Dubai + UAE, then HR moved him to KSA in ERP."""
    ravi = _person(db, "ravi", ticks=("DUBAI", "UAE"))
    user = _sign_in(db, monkeypatch, ravi, "KSA")
    assert user["allowed_regions"][0] == "KSA"  # home first
    assert sorted(user["allowed_regions"]) == ["DUBAI", "KSA", "UAE"]
    assert user["region_code"] == "KSA"  # starts in the (new) home company


def test_ticks_saved_without_home_still_offer_home(db, monkeypatch):
    """Fatima's ticks were written outside Admin -> People and miss her home company."""
    fatima = _person(db, "fatima", ticks=("UAE", "KSA", "OMAN"))
    user = _sign_in(db, monkeypatch, fatima, "DUBAI")
    assert user["allowed_regions"] == ["DUBAI", "KSA", "OMAN", "UAE"]
    assert user["region_code"] == "DUBAI"


def test_single_company_user_unchanged(db, monkeypatch):
    dev_ksa = _person(db, "dev_ksa")
    assert selectable_regions_for(db, dev_ksa, "KSA") == []  # no ticks -> not multi-company
    user = _sign_in(db, monkeypatch, dev_ksa, "KSA")
    assert user["allowed_regions"] == ["KSA"]


def test_no_company_in_erp_falls_back_to_dubai(db, monkeypatch):
    """Dubai (Blue Rhine Industries), not UAE (Contracting, no ERP subsidiary)."""
    raghu = _person(db, "raghu")
    user = _sign_in(db, monkeypatch, raghu, None)
    assert user["region_code"] == "DUBAI"
    assert user["allowed_regions"] == ["DUBAI"]


def test_can_switch_to_unticked_home_but_not_elsewhere(db, monkeypatch):
    ravi = _person(db, "ravi", ticks=("DUBAI", "UAE"))
    monkeypatch.setattr(routes_auth, "resolve_default_region_code", lambda _db, _id: "KSA")
    current = CurrentUser(ravi.user_id, "ravi", "employee", region_code="DUBAI")

    out = routes_auth.switch_region(routes_auth.SwitchRegionRequest(region_code="KSA"), current, db)
    assert out.user["region_code"] == "KSA"
    with pytest.raises(HTTPException) as exc:
        routes_auth.switch_region(routes_auth.SwitchRegionRequest(region_code="OMAN"), current, db)
    assert exc.value.status_code == 403
