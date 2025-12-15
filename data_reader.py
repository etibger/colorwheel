"""
Module for reading pen and ink data from an ODS spreadsheet.
"""

import logging
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from typing import Dict, List

# set up module logger
logger = logging.getLogger(__name__)


@dataclass
class FountainPen:
    brand: str
    name: str
    nib_size: str
    body_color: str


@dataclass
class Ink:
    brand: str
    name: str
    color_srgb: List[str]
    color_rgb_hex: int


@dataclass
class PenSetup:
    pen: FountainPen
    ink: Ink


class DataReader:
    """
    Reads fountain pen and ink data from an ODS file.
    Expects a sheet with columns: Type, Brand, Name, Details, Color
    where Type is 'pen' or 'ink', Details is nib size for pens.
    """

    def __init__(self, filepath: str):
        logger.debug(f"Setup new instance (name:{id(self)}) of DataReader: {filepath}")
        self.filepath = filepath
        self.raw_rows = self.read()
        self.pens = self.create_pens(self.raw_rows)
        self.inks = self.create_inks(self.raw_rows)
        self.setups = self.create_setups(self.pens, self.inks)

    def _get_content_xml(self) -> ET.Element:
        with zipfile.ZipFile(self.filepath, "r") as z:
            with z.open("content.xml") as f:
                return ET.parse(f).getroot()

    def read(self) -> List[Dict[str, str]]:
        """
        Parse the ODS and return raw rows as dicts.
        Each dict has keys: pen_brand, pen_name, nib_size, ink_brand, color_name,
        srgb_h, srgb_s, srgb_v, rgb_hex.
        """
        logger.debug(f"Reading ODS file: {self.filepath}")
        root = self._get_content_xml()
        ns = {
            "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
            "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
        }
        raw_rows: List[Dict[str, str]] = []
        table = root.find(".//table:table", ns)
        if table is None:
            logger.warning("No table found in ODS content.xml")
            return raw_rows
        # Define column keys for mapping
        keys = [
            "pen_brand",
            "pen_name",
            "nib_size",
            "ink_brand",
            "color_name",
            "srgb_h",
            "srgb_s",
            "srgb_v",
            "rgb_hex",
        ]
        for row in table.findall("table:table-row", ns):
            cells = row.findall("table:table-cell", ns)
            texts: List[str] = []
            for cell in cells:
                text_el = cell.find("text:p", ns)
                texts.append(text_el.text if text_el is not None else "")
            if len(texts) < len(keys):
                logger.debug("Line skipped:")
                logger.debug(texts)
                continue
            if texts[0] == "Pen Brand":
                logger.debug("Header found:")
                logger.debug(texts)
                continue
            # Map first n columns to dict
            row_dict = dict(zip(keys, texts[: len(keys)]))
            logger.debug(f"Parsed row: {row_dict}")
            raw_rows.append(row_dict)
        logger.debug(f"Returned {len(raw_rows)} number of rows.")
        return raw_rows

    def create_pens(self, raw_rows: List[Dict[str, str]]) -> List[FountainPen]:
        """
        Create FountainPen objects from raw data rows.
        """
        logger.debug(f"Creating pens from {len(raw_rows)} rows")
        pens: List[FountainPen] = []
        for row in raw_rows:
            pens.append(
                FountainPen(
                    brand=row.get("pen_brand", ""),
                    name=row.get("pen_name", ""),
                    nib_size=row.get("nib_size", ""),
                    # add body_color determination from pen_name
                    # e.g. Pilot Metropolitan [fekete]
                    body_color="TBD",
                )
            )
        return pens

    def create_inks(self, raw_rows: List[Dict[str, str]]) -> List[Ink]:
        """
        Create Ink objects from raw data rows.
        """
        logger.debug(f"Creating inks from {len(raw_rows)} rows")
        inks: List[Ink] = []
        for row in raw_rows:
            inks.append(
                Ink(
                    brand=row.get("ink_brand", ""),
                    name=row.get("color_name", ""),
                    color_srgb=[
                        row.get("srgb_h", ""),
                        row.get("srgb_s", ""),
                        row.get("srgb_v", ""),
                    ],
                    color_rgb_hex=row.get("rgb_hex", ""),
                )
            )
        return inks

    # REVISIT we need different data structure for pens/inks to easily find
    # the matched ink and pens
    def create_setups(self, pens: List[FountainPen], inks: List[Ink]) -> List[PenSetup]:
        """
        Pair pens and inks in order to create a list of PenSetup.
        """
        setups: List[PenSetup] = []
        for pen, ink in zip(pens, inks):
            setups.append(PenSetup(pen=pen, ink=ink))
        return setups

    def load_setups(self) -> List[PenSetup]:
        """
        Convenience method: read raw data, create pen and ink objects,
        and pair them into PenSetup instances.
        """
        logger.debug(
            "Loading setups: read -> create_pens -> create_inks -> create_setups"
        )
        raw_rows = self.read()
        pens = self.create_pens(raw_rows)
        inks = self.create_inks(raw_rows)
        setups = self.create_setups(pens, inks)
        logger.info(f"Loaded {len(setups)} pen setups")
        return setups
