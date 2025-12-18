import filecmp
from pathlib import Path

import pytest

from main import generate_wheel_from_db


@pytest.mark.parametrize(
    "db_file, output_png, expected_png",
    [
        ("data/golden.db", "tmp_wheel.png", "data/golden.png"),
    ],
)
def test_db_to_png_conversion(tmp_path, db_file, output_png, expected_png):
    """Test generating a color wheel PNG from an existing DB."""
    db_path = Path(db_file)
    assert db_path.exists(), f"DB file {db_file} missing"

    out_path = tmp_path / output_png
    # Generate PNG
    result = generate_wheel_from_db(str(db_path), str(out_path))
    assert result.exists(), "Output PNG was not created"

    # Compare with expected golden image
    expected = Path(expected_png)
    assert expected.exists(), f"Golden image {expected_png} missing"
    # Use byte-level comparison for exact match
    assert filecmp.cmp(result, expected, shallow=False), (
        "Generated PNG differs from golden reference"
    )
