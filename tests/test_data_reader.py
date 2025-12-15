import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import pytest

from data_reader import DataReader, FountainPen, Ink, PenSetup


@pytest.fixture
def sample_ods(tmp_path):
    # Create a minimal ODS-like ZIP with content.xml
    content = '''<?xml version="1.0"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
  <office:body>
    <office:spreadsheet>
      <table:table table:name="Sheet1">
        <table:table-row>
          <table:table-cell><text:p>pen</text:p></table:table-cell>
          <table:table-cell><text:p>Parker</text:p></table:table-cell>
          <table:table-cell><text:p>51</text:p></table:table-cell>
          <table:table-cell><text:p>Fine</text:p></table:table-cell>
          <table:table-cell><text:p>Black</text:p></table:table-cell>
        </table:table-row>
        <table:table-row>
          <table:table-cell><text:p>ink</text:p></table:table-cell>
          <table:table-cell><text:p>Parker</text:p></table:table-cell>
          <table:table-cell><text:p>Quink</text:p></table:table-cell>
          <table:table-cell><text:p></text:p></table:table-cell>
          <table:table-cell><text:p>Blue</text:p></table:table-cell>
        </table:table-row>
      </table:table>
    </office:spreadsheet>
  </office:body>
</office:document-content>'''
    ods_path = tmp_path / "sample.ods"
    with zipfile.ZipFile(ods_path, 'w') as zf:
        zf.writestr('content.xml', content)
    return str(ods_path)


def test_read_returns_dicts(sample_ods):
    reader = DataReader(sample_ods)
    rows = reader.read()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)
    assert rows[0]['type'] == 'pen'
    assert rows[1]['type'] == 'ink'

def test_create_pens_and_inks(sample_ods):
    reader = DataReader(sample_ods)
    rows = reader.read()
    pens = reader.create_pens(rows)
    inks = reader.create_inks(rows)
    assert len(pens) == 1
    assert isinstance(pens[0], FountainPen)
    assert pens[0].brand == 'Parker'
    assert len(inks) == 1
    assert isinstance(inks[0], Ink)
    assert inks[0].name == 'Quink'

def test_load_setups(sample_ods):
    reader = DataReader(sample_ods)
    setups = reader.load_setups()
    assert len(setups) == 1
    setup = setups[0]
    assert isinstance(setup, PenSetup)
    assert setup.pen.name == '51'
    assert setup.ink.color == 'Blue'
