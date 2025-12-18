import tempfile
import zipfile
from pathlib import Path

import pytest

# ODS sample content for pytest fixtures (header + one data row)
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
          <table:table-cell><text:p>#0000FF</text:p></table:table-cell>
        </table:table-row>
      </table:table>
    </office:spreadsheet>
  </office:body>
</office:document-content>"""


@pytest.fixture
def sample_ods():
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name) / "sample.ods"
    # write content.xml inside ODS zip
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("content.xml", SAMPLE_CONTENT)
    yield str(path)
    tmp.cleanup()
