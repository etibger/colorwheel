import tempfile
import unittest
import zipfile
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from storage.orm import FountainPen, Ink, PenSetup, load_data_from_ods

# Minimal ODS content for testing
SAMPLE_XML = """<?xml version="1.0"?>
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
          <table:table-cell><text:p>Pen Body color</text:p></table:table-cell>
          <table:table-cell><text:p>Nib size</text:p></table:table-cell>
          <table:table-cell><text:p>Ink Brand</text:p></table:table-cell>
          <table:table-cell><text:p>Color Name</text:p></table:table-cell>
          <table:table-cell><text:p>0.0</text:p></table:table-cell>
          <table:table-cell><text:p>1.0</text:p></table:table-cell>
          <table:table-cell><text:p>1.0</text:p></table:table-cell>
          <table:table-cell><text:p>rgb_hex</text:p></table:table-cell>
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


def create_ods(path: Path):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("content.xml", SAMPLE_XML)


class TestORM(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.ods_path = Path(self.tmpdir.name) / "sample.ods"
        create_ods(self.ods_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_load_data_and_query(self):
        db_file = Path(self.tmpdir.name) / "test.db"
        engine = load_data_from_ods(str(self.ods_path), str(db_file))
        Session = sessionmaker(bind=engine)
        session = Session()
        self.assertEqual(session.query(FountainPen).count(), 1)
        self.assertEqual(session.query(Ink).count(), 1)
        self.assertEqual(session.query(PenSetup).count(), 1)
        session.close()

    def test_plain_file_path(self):
        db_file = Path(self.tmpdir.name) / "plain.db"
        engine = load_data_from_ods(str(self.ods_path), str(db_file))
        self.assertTrue(db_file.exists())
        Session = sessionmaker(bind=engine)
        session = Session()
        self.assertEqual(session.query(FountainPen).count(), 1)
        self.assertEqual(session.query(Ink).count(), 1)
        self.assertEqual(session.query(PenSetup).count(), 1)
        session.close()


if __name__ == "__main__":
    unittest.main()
