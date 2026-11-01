"""scripts/backfill_home_regions: saves each user's ERP home company in bulk, dry-run first."""
import os

for _k in ("READER_DB_SERVER", "READER_DB_NAME", "READER_DB_USER", "READER_DB_PASSWORD"):
    os.environ.setdefault(_k, "test")

import json  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from database.models import (  # noqa: E402
    Base,
    ErpAuthExpenseUsers,
    ErpExpenseMultiRegionUserRegion,
    ErpExpenseRegionConfig,
    ErpMasterExpenseRole,
)
from scripts import backfill_home_regions as script  # noqa: E402


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    # Minimal ERP master tables -- the script reads them with raw SQL, like login does.
    for ddl in (
        "CREATE TABLE ErpMasterSubsidiary (subsidiaryId INTEGER PRIMARY KEY, subsidiaryCode TEXT)",
        "CREATE TABLE ErpMasterRegion (regionId INTEGER PRIMARY KEY, subsidiaryId INTEGER)",
        "CREATE TABLE ErpMasterEmployee (employeeId INTEGER PRIMARY KEY, userId INTEGER, regionId INTEGER)",
    ):
        session.execute(text(ddl))
    session.execute(text(
        "INSERT INTO ErpMasterSubsidiary VALUES (1, 'BRI UAE'), (2, 'Prosigns KSA'), (3, 'Mystery Co')"
    ))
    session.execute(text("INSERT INTO ErpMasterRegion VALUES (10, 1), (20, 2), (30, 3)"))
    yield session
    session.close()


def _setup(db):
    roles = {code: ErpMasterExpenseRole(role_code=code, role_name=code) for code in
             ("employee", "hod", "accountant", "finance_manager")}
    db.add_all(roles.values())
    matrix = json.dumps({"stages": ["accountant"]})
    dubai = ErpExpenseRegionConfig(region_code="DUBAI", region_name="Dubai", approval_matrix_json=matrix)
    ksa = ErpExpenseRegionConfig(region_code="KSA", region_name="KSA", approval_matrix_json=matrix)
    db.add_all([dubai, ksa])
    db.flush()

    def person(name, role, erp_region=None, home=None):
        u = ErpAuthExpenseUsers(user_name=name, display_name=name, password_hash="x",
                                role_id=roles[role].role_id, home_region_id=home)
        db.add(u)
        db.flush()
        if erp_region:
            db.execute(text("INSERT INTO ErpMasterEmployee (userId, regionId) VALUES (:u, :r)"),
                       {"u": u.user_id, "r": erp_region})
        return u

    people = {
        "dubai_acct": person("dubai_acct", "accountant", erp_region=10),
        "ksa_fm": person("ksa_fm", "finance_manager", erp_region=20),
        "already": person("already", "employee", erp_region=10, home=dubai.region_id),
        "moved": person("moved", "hod", erp_region=20, home=dubai.region_id),  # ERP now says KSA
        "no_erp": person("no_erp", "hod"),
        "unmapped": person("unmapped", "accountant", erp_region=30),
        "ticked": person("ticked", "hod"),
    }
    db.add(ErpExpenseMultiRegionUserRegion(user_id=people["ticked"].user_id, region_id=ksa.region_id, is_active=1))
    db.commit()
    return people, dubai, ksa


def test_dry_run_reports_but_saves_nothing(db, capsys):
    people, _, _ = _setup(db)
    assert script.run(db, apply=False) == 0
    out = capsys.readouterr().out

    db.expire_all()
    assert people["dubai_acct"].home_region_id is None
    assert "to set / change:   3" in out
    assert "Dry-run only" in out
    # Approvers that stay open to every company are called out; the ticked one isn't.
    warning = out.split("WARNING:")[1]
    assert "no_erp (hod)" in warning and "unmapped (accountant)" in warning
    assert "ticked" not in warning


def test_apply_saves_erp_home_company(db):
    people, dubai, ksa = _setup(db)
    assert script.run(db, apply=True) == 0
    db.expire_all()

    assert people["dubai_acct"].home_region_id == dubai.region_id
    assert people["ksa_fm"].home_region_id == ksa.region_id
    assert people["already"].home_region_id == dubai.region_id
    assert people["moved"].home_region_id == ksa.region_id  # ERP wins, same as login
    assert people["no_erp"].home_region_id is None
    assert people["unmapped"].home_region_id is None


def test_after_backfill_ksa_fm_no_longer_covers_dubai(db):
    from services.region_scope import user_covers

    people, dubai, ksa = _setup(db)
    assert user_covers(db, people["ksa_fm"].user_id, dubai.region_id)  # unrestricted before
    script.run(db, apply=True)
    assert not user_covers(db, people["ksa_fm"].user_id, dubai.region_id)
    assert user_covers(db, people["ksa_fm"].user_id, ksa.region_id)


def test_second_run_has_nothing_to_do(db, capsys):
    _setup(db)
    script.run(db, apply=True)
    capsys.readouterr()
    script.run(db, apply=True)
    assert "Nothing to save." in capsys.readouterr().out
