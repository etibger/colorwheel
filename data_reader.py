"""
.. module:: data_reader
   :noindex:
   :synopsis: Read pen and ink data from an ODS spreadsheet.

This module parses an OpenDocument Spreadsheet (ODS) to extract fountain pen
and ink information into Python data structures.
"""

import hashlib
import logging
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass  # used for data models
from typing import Dict, List

# set up module logger
logger = logging.getLogger(__name__)


@dataclass
class FountainPen:
    """
    Represents a fountain pen entry extracted from ODS.

    :param id: Unique pen identifier (SHA-256 hash).
    :type id: int
    :param brand: Manufacturer or brand of the pen.
    :type brand: str
    :param name: Model name of the pen.
    :type name: str
    :param nib_size: Nib size descriptor (e.g., 'M', 'F').
    :type nib_size: str
    :param body_color: Hex color code of the pen body.
    :type body_color: str
    """
    id: int
    brand: str
    name: str
    nib_size: str
    body_color: str



@dataclass
class Ink:
    """
    Represents an ink entry extracted from ODS.

    :param id: Unique ink identifier (SHA-256 hash).
    :type id: int
    :param brand: Manufacturer or brand of the ink.
    :type brand: str
    :param name: Name of the ink color.
    :type name: str
    :param color_srgb: List of HSV components as strings.
    :type color_srgb: list[str]
    :param color_rgb_hex: Hex color code of the ink.
    :type color_rgb_hex: str
    """
    id: int
    brand: str
    name: str
    color_srgb: List[str]
    color_rgb_hex: str



@dataclass
class PenSetup:
    """
    Represents a pen and ink pairing.

    :param id: Unique setup identifier (SHA-256 hash).
    :type id: int
    :param pen_id: Identifier of the associated FountainPen.
    :type pen_id: int
    :param ink_id: Identifier of the associated Ink.
    :type ink_id: int
    """
    id: int
    pen_id: int
    ink_id: int



class DataReader:
    """
    Read fountain pen and ink data from an ODS spreadsheet.

    :param filepath: Path to the ODS file.
    :type filepath: str
    :ivar pens: Mapping of pen_id to FountainPen instances.
    :ivar inks: Mapping of ink_id to Ink instances.
    :ivar setups: Mapping of setup_id to PenSetup instances.
    """

    def __init__(self, filepath: str):
        logger.debug(f"Setup new instance (name:{id(self)}) of DataReader: {filepath}")
        self.filepath = filepath
        self.raw_rows = self.read()
        self.pens = self.create_pens(self.raw_rows)
        self.inks = self.create_inks(self.raw_rows)
        self.setups = self.create_setups(self.raw_rows, self.pens, self.inks)

    def _get_content_xml(self) -> ET.Element:
        """
        Extract and parse the ODS content.xml file.

        :returns: Root Element of the parsed XML tree.
        :rtype: xml.etree.ElementTree.Element
        """
        with zipfile.ZipFile(self.filepath, "r") as z:
            with z.open("content.xml") as f:
                return ET.parse(f).getroot()

    def read(self) -> List[Dict[str, str]]:
        """
        Parse the ODS spreadsheet into raw row dictionaries.

        :returns: List of row dictionaries with keys:
                  pen_brand, pen_name, pen_body_color, nib_size,
                  ink_brand, color_name, srgb_h, srgb_s, srgb_v, rgb_hex
        :rtype: list[dict[str,str]]
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
        Instantiate FountainPen objects from raw row data.

        :param raw_rows: Parsed raw row dictionaries.
        :type raw_rows: list[dict[str,str]]
        :returns: Mapping of pen_id to FountainPen instances.
        :rtype: dict[int, FountainPen]
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
            # Use positional args to avoid keyword-init mismatch
            pens[pen_id] = FountainPen(
                pen_id,
                brand,
                name,
                row.get("nib_size", ""),
                body_color,
            )
        return pens

    def create_inks(self, raw_rows: List[Dict[str, str]]) -> Dict[int, Ink]:
        """
        Instantiate Ink objects from raw row data.

        :param raw_rows: Parsed raw row dictionaries.
        :type raw_rows: list[dict[str,str]]
        :returns: Mapping of ink_id to Ink instances.
        :rtype: dict[int, Ink]
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
            # Use positional args to avoid keyword-init mismatch
            inks[ink_id] = Ink(
                ink_id,
                brand,
                name,
                [row.get("srgb_h", ""), row.get("srgb_s", ""), row.get("srgb_v", "")],
                hex_code,
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
        Instantiate PenSetup objects linking pens to inks.

        :param raw_rows: Parsed raw row dictionaries.
        :type raw_rows: list[dict[str,str]]
        :param pens: Mapping of pen_id to FountainPen.
        :type pens: dict[int, FountainPen]
        :param inks: Mapping of ink_id to Ink.
        :type inks: dict[int, Ink]
        :returns: Mapping of setup_id to PenSetup instances.
        :rtype: dict[int, PenSetup]
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
            # Use positional args to avoid keyword-init mismatch
            setups[setup_id] = PenSetup(setup_id, pen_id, ink_id)
        return setups
