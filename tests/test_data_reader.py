import tempfile
import unittest
import zipfile
from pathlib import Path

from storage.data_reader import DataReader, FountainPen, Ink, PenSetup

SAMPLE_CONTENT = """<?xml version="1.0"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
  <office:body>
    <office:spreadsheet>
      <table:table table:name="Sheet1">
        <!-- header row -->
        <table:table-row>
          <table:table-cell><text:p>Pen Brand</text:p></table:table-cell>
          <table:table-cell><text:p>Pen Name</text:p></table:table-cell>
          <table:table-cell><text:p>Pen Body Color</text:p></table:table-cell>
          <table:table-cell><text:p>Nib Size</text:p></table:table-cell>
          <table:table-cell><text:p>Ink Brand</text:p></table:table-cell>
          <table:table-cell><text:p>Color Name</text:p></table:table-cell>
          <table:table-cell><text:p>0.0</text:p></table:table-cell>
          <table:table-cell><text:p>1.0</text:p></table:table-cell>
          <table:table-cell><text:p>1.0</text:p></table:table-cell>
          <table:table-cell><text:p>#FFFFFF</text:p></table:table-cell>
        </table:table-row>
        <!-- data row -->
        <table:table-row>
          <table:table-cell><text:p>Parker</text:p></table:table-cell>
          <table:table-cell><text:p>51</text:p></table:table-cell>
          <table:table-cell><text:p>Purple</text:p></table:table-cell>
          <table:table-cell><text:p>Fine</text:p></table:table-cell>
          <table:table-cell><text:p>Parker</text:p></table:table-cell>
          <table:table-cell><text:p>Quink</text:p></table:table-cell>
          <table:table-cell><text:p>0.0</text:p></table:table-cell>
          <table:table-cell><text:p>1.0</text:p></table:table-cell>
          <table:table-cell><text:p>1.0</text:p></table:table-cell>
          <table:table-cell><text:p>0000FF</text:p></table:table-cell>
        </table:table-row>
      </table:table>
    </office:spreadsheet>
  </office:body>
</office:document-content>"""


def create_sample_ods(path: Path):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("content.xml", SAMPLE_CONTENT)


class TestDataReader(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.ods_path = Path(self.tmpdir.name) / "sample.ods"
        create_sample_ods(self.ods_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_read_returns_dicts(self):
        reader = DataReader(str(self.ods_path))
        rows = reader.raw_rows
        self.assertIsInstance(rows, list)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        keys = [
            "pen_brand",
            "pen_name",
            "pen_body_color",
            "nib_size",
            "ink_brand",
            "color_name",
            "srgb_h",
            "srgb_s",
            "srgb_v",
            "rgb_hex",
        ]
        for k in keys:
            self.assertIn(k, row)

    def test_create_pens_and_inks(self):
        reader = DataReader(str(self.ods_path))
        pens = reader.pens
        inks = reader.inks
        self.assertIsInstance(pens, dict)
        self.assertIsInstance(inks, dict)
        self.assertEqual(len(pens), 1)
        pen = next(iter(pens.values()))
        self.assertIsInstance(pen, FountainPen)
        self.assertEqual(pen.brand, "Parker")
        self.assertEqual(pen.nib_size, "Fine")
        self.assertEqual(len(inks), 1)
        ink = next(iter(inks.values()))
        self.assertIsInstance(ink, Ink)
        self.assertEqual(ink.name, "Quink")
        self.assertEqual(ink.color_rgb_hex, "0000FF")

    def test_load_setups(self):
        reader = DataReader(str(self.ods_path))
        setups = reader.setups
        self.assertIsInstance(setups, dict)
        self.assertEqual(len(setups), 1)
        setup = next(iter(setups.values()))
        # setup should be a PenSetup instance
        self.assertIsInstance(setup, PenSetup)
        pen = reader.pens[setup.pen_id]
        ink = reader.inks[setup.ink_id]
        self.assertEqual(pen.name, "51")
        self.assertEqual(ink.name, "Quink")
        self.assertEqual(ink.color_srgb, ["0.0", "1.0", "1.0"])
        self.assertEqual(ink.color_rgb_hex, "0000FF")


if __name__ == "__main__":
    unittest.main()


def test_read_returns_dicts(sample_ods):
    reader = DataReader(sample_ods)
    rows = reader.raw_rows
    # should skip header, so only one data row
    assert isinstance(rows, list)
    assert len(rows) == 1
    row = rows[0]
    # check expected keys
    keys = [
        "pen_brand",
        "pen_name",
        "pen_body_color",
        "nib_size",
        "ink_brand",
        "color_name",
        "srgb_h",
        "srgb_s",
        "srgb_v",
        "rgb_hex",
    ]
    assert all(k in row for k in keys)


def test_create_pens_and_inks(sample_ods):
    reader = DataReader(sample_ods)
    pens = reader.pens
    inks = reader.inks
    # pens and inks are dicts keyed by id
    assert isinstance(pens, dict)
    assert isinstance(inks, dict)
    assert len(pens) == 1
    # inspect the single pen
    pen = next(iter(pens.values()))
    assert isinstance(pen.id, int)
    assert isinstance(pen, FountainPen)
    assert pen.brand == "Parker"
    assert pen.nib_size == "Fine"
    assert len(inks) == 1
    ink = next(iter(inks.values()))
    assert isinstance(ink.id, int)
    assert isinstance(ink, Ink)
    assert ink.name == "Quink"
    assert ink.color_rgb_hex == "0000FF"


def test_load_setups(sample_ods):
    reader = DataReader(sample_ods)
    setups = reader.setups
    # setups is a dict keyed by setup id
    assert isinstance(setups, dict)
    assert len(setups) == 1
    setup = next(iter(setups.values()))
    # setup id should be int and reference pen and ink by id
    assert isinstance(setup.id, int)
    assert isinstance(setup, PenSetup)
    # look up referenced pen and ink
    pen = reader.pens[setup.pen_id]
    ink = reader.inks[setup.ink_id]
    assert pen.name == "51"
    assert ink.name == "Quink"
    assert ink.color_srgb == ["0.0", "1.0", "1.0"]
    assert ink.color_rgb_hex == "0000FF"
