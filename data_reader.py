"""
Module for reading pen and ink data from an ODS spreadsheet.
"""

import hashlib
import logging
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from typing import Dict, List

# set up module logger
logger = logging.getLogger(__name__)


@dataclass
class FountainPen:
    id: int
    brand: str
    name: str
    nib_size: str
    body_color: str


@dataclass
class Ink:
    id: int
    brand: str
    name: str
    color_srgb: List[str]
    color_rgb_hex: str


@dataclass
class PenSetup:
    """Represents a pen+ink pairing by their IDs."""

    id: int
    pen_id: int
    ink_id: int


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
        self.setups = self.create_setups(self.raw_rows, self.pens, self.inks)

    def _get_content_xml(self) -> ET.Element:
        with zipfile.ZipFile(self.filepath, "r") as z:
            with z.open("content.xml") as f:
                return ET.parse(f).getroot()

    def read(self) -> List[Dict[str, str]]:
        """
        Parse the ODS and return raw rows as dicts.
        Each dict has keys: pen_brand, pen_name, pen_body_color, nib_size, ink_brand,
        color_name, srgb_h, srgb_s, srgb_v, rgb_hex.
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
            "pen_body_color",
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

    def create_pens(self, raw_rows: List[Dict[str, str]]) -> Dict[int, FountainPen]:
        """
        Create FountainPen objects from raw data rows.
        """
        logger.debug(f"Creating pens from {len(raw_rows)} rows")
        pens: Dict[int, FountainPen] = {}
        for row in raw_rows:
            # compute SHA-256-based id from pen fields
            brand = row.get("pen_brand", "")
            name = row.get("pen_name", "")
            body_color = row.get("pen_body_color", "")
            raw = "|".join([brand, name, body_color]).encode("utf-8")
            pen_id = int.from_bytes(hashlib.sha256(raw).digest(), "big")
            pens[pen_id] = FountainPen(
                id=pen_id,
                brand=brand,
                name=name,
                nib_size=row.get("nib_size", ""),
                body_color=body_color,
            )
        return pens

    def create_inks(self, raw_rows: List[Dict[str, str]]) -> Dict[int, Ink]:
        """
        Create Ink objects from raw data rows, keyed by SHA-256 id.
        """
        logger.debug(f"Creating inks from {len(raw_rows)} rows")
        inks: Dict[int, Ink] = {}
        for row in raw_rows:
            # compute SHA-256-based id from ink fields
            brand = row.get("ink_brand", "")
            name = row.get("color_name", "")
            raw = "|".join([brand, name]).encode("utf-8")
            ink_id = int.from_bytes(hashlib.sha256(raw).digest(), "big")
            # Normalize hex code by stripping leading '#'
            raw_hex = row.get("rgb_hex", "") or ""
            hex_code = raw_hex.lstrip('#')
            inks[ink_id] = Ink(
                id=ink_id,
                brand=brand,
                name=name,
                color_srgb=[
                    row.get("srgb_h", ""),
                    row.get("srgb_s", ""),
                    row.get("srgb_v", ""),
                ],
                color_rgb_hex=hex_code,
            )
        return inks

    # REVISIT we need different data structure for pens/inks to easily find
    # the matched ink and pens
    def create_setups(
        self,
        raw_rows: List[Dict[str, str]],
        pens: Dict[int, FountainPen],
        inks: Dict[int, Ink],
    ) -> Dict[int, PenSetup]:
        """
        Create PenSetup objects keyed by SHA-256 id, mapping raw row pairs.
        """
        setups: Dict[int, PenSetup] = {}
        for row in raw_rows:
            # recompute pen_id and ink_id
            p_raw = "|".join(
                [
                    row.get("pen_brand", ""),
                    row.get("pen_name", ""),
                    row.get("pen_body_color", ""),
                ]
            ).encode("utf-8")
            pen_id = int.from_bytes(hashlib.sha256(p_raw).digest(), "big")
            i_raw = "|".join(
                [
                    row.get("ink_brand", ""),
                    row.get("color_name", ""),
                ]
            ).encode("utf-8")
            ink_id = int.from_bytes(hashlib.sha256(i_raw).digest(), "big")
            # compute setup_id
            s_raw = f"{pen_id}|{ink_id}".encode("utf-8")
            setup_id = int.from_bytes(hashlib.sha256(s_raw).digest(), "big")
            setups[setup_id] = PenSetup(id=setup_id, pen_id=pen_id, ink_id=ink_id)
        return setups
