import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from extraction.reference_data import CategoryRef, ReferenceData


@pytest.fixture
def default_reference_data() -> ReferenceData:
    return ReferenceData()


def reference_data_with(vendors=(), categories=(), **overrides) -> ReferenceData:
    return ReferenceData(known_vendors=tuple(vendors), categories=tuple(categories), **overrides)
