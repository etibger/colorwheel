# conftest.py: Global pytest fixtures and warning filters
# conftest.py: Global pytest fixtures and warning filters
import warnings
import zipfile

import pytest

# Suppress all ResourceWarnings (e.g., unclosed DB connections) during tests
warnings.filterwarnings("ignore", category=ResourceWarning)

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


@pytest.fixture
def sample_ods(tmp_path):
    """Create a sample ODS file fixture with minimal spreadsheet content."""
    ods_path = tmp_path / "sample.ods"
    with zipfile.ZipFile(ods_path, "w") as zf:
        zf.writestr("content.xml", SAMPLE_CONTENT)
    return str(ods_path)
