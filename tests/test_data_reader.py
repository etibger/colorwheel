import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import pytest

from data_reader import DataReader, FountainPen, Ink, PenSetup


@pytest.fixture
def sample_ods(tmp_path):
    # Create a minimal ODS-like ZIP with content.xml
    # Mimic header row plus one data row matching new schema
    content = '''<?xml version="1.0"?>
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
</office:document-content>'''
    ods_path = tmp_path / "sample.ods"
    with zipfile.ZipFile(ods_path, 'w') as zf:
        zf.writestr('content.xml', content)
    return str(ods_path)


def test_read_returns_dicts(sample_ods):
    reader = DataReader(sample_ods)
    rows = reader.raw_rows
    # should skip header, so only one data row
    assert isinstance(rows, list)
    assert len(rows) == 1
    row = rows[0]
    # check expected keys
    keys = ['pen_brand','pen_name','nib_size','ink_brand','color_name','srgb_h','srgb_s','srgb_v','rgb_hex']
    assert all(k in row for k in keys)

def test_create_pens_and_inks(sample_ods):
    reader = DataReader(sample_ods)
    pens = reader.pens
    inks = reader.inks
    assert len(pens) == 1
    assert isinstance(pens[0], FountainPen)
    assert pens[0].brand == 'Parker'
    assert pens[0].nib_size == 'Fine'
    assert len(inks) == 1
    assert isinstance(inks[0], Ink)
    assert inks[0].name == 'Quink'
    assert inks[0].color_rgb_hex == '0000FF'

def test_load_setups(sample_ods):
    reader = DataReader(sample_ods)
    setups = reader.setups
    assert len(setups) == 1
    setup = setups[0]
    assert isinstance(setup, PenSetup)
    assert setup.pen.name == '51'
    assert setup.ink.name == 'Quink'
    assert setup.ink.color_srgb == ['0.0','1.0','1.0']
    assert setup.ink.color_rgb_hex == '0000FF'
