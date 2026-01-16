"""
SQLAlchemy ORM for FountainPens, Inks, and PenSetups.
"""

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from storage.data_reader import DataReader

Base = declarative_base()


class FountainPen(Base):
    __tablename__ = "fountain_pens"

    # Store SHA-256 IDs as hex strings to avoid integer overflow
    # primary key stored as hex string
    # use TEXT affinity for hex IDs
    id = Column(String, primary_key=True)
    brand = Column(String, nullable=False)
    name = Column(String, nullable=False)
    nib_size = Column(String)
    body_color = Column(String)

    setups = relationship("PenSetup", back_populates="pen")


class Ink(Base):
    __tablename__ = "inks"

    id = Column(String, primary_key=True)
    brand = Column(String, nullable=False)
    name = Column(String, nullable=False)
    srgb_h = Column(Float)
    srgb_s = Column(Float)
    srgb_v = Column(Float)
    rgb_hex = Column(String)

    setups = relationship("PenSetup", back_populates="ink")


class PenSetup(Base):
    __tablename__ = "pen_setups"

    id = Column(String, primary_key=True)
    pen_id = Column(String, ForeignKey("fountain_pens.id"), nullable=False)
    ink_id = Column(String, ForeignKey("inks.id"), nullable=False)

    pen = relationship("FountainPen", back_populates="setups")
    ink = relationship("Ink", back_populates="setups")


def init_db(db_url: str):
    """
    Initialize the database engine and create tables.

    Returns:
        Engine: SQLAlchemy Engine instance.
    """
    engine = create_engine(db_url)
    # Drop existing tables to reset schema
    Base.metadata.drop_all(engine)
    # Create tables according to current models
    Base.metadata.create_all(engine)
    return engine


def load_data_from_ods(ods_path: str, db_url: str):
    """
    Read pens, inks, and setups from an ODS file and persist them to the database.

    Args:
        ods_path: Path to the ODS data file.
        db_url: Database URL (e.g., 'sqlite:///pens.db').

    Returns:
        Engine: SQLAlchemy Engine connected to the database.
    """
    # Interpret db_url as filesystem path if no scheme or sqlite URL
    from pathlib import Path as _Path

    db_file = None
    if db_url.startswith("sqlite:///"):
        # strip sqlite:/// prefix
        db_file = _Path(db_url[len("sqlite:///") :])
    elif "://" not in db_url:
        db_file = _Path(db_url)
        db_url = f"sqlite:///{db_file}"
    # Ensure fresh database file for SQLite
    if db_file:
        db_file.parent.mkdir(parents=True, exist_ok=True)
        if db_file.exists():
            db_file.unlink()
    # parse ODS file
    reader = DataReader(ods_path)

    # initialize DB
    engine = init_db(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # insert FountainPen entries
    for pen in reader.pens.values():
        pen_hex = f"{pen.id:064x}"
        session.add(
            FountainPen(
                id=pen_hex,
                brand=pen.brand,
                name=pen.name,
                nib_size=pen.nib_size,
                body_color=pen.body_color,
            )
        )
    # insert Ink entries
    for ink in reader.inks.values():
        # parse sRGB floats
        try:
            h, s, v = [float(x) for x in ink.color_srgb]
        except Exception:
            h = s = v = None
        ink_hex = f"{ink.id:064x}"
        session.add(
            Ink(
                id=ink_hex,
                brand=ink.brand,
                name=ink.name,
                srgb_h=h,
                srgb_s=s,
                srgb_v=v,
                rgb_hex=ink.color_rgb_hex,
            )
        )
    # insert PenSetup entries
    for setup in reader.setups.values():
        # use hex strings for IDs
        setup_hex = f"{setup.id:064x}"
        pen_hex = f"{setup.pen_id:064x}"
        ink_hex = f"{setup.ink_id:064x}"
        session.add(
            PenSetup(
                id=setup_hex,
                pen_id=pen_hex,
                ink_id=ink_hex,
            )
        )

    session.commit()
    session.close()
    # Dispose engine to close all connections and avoid warnings
    try:
        engine.dispose()
    except Exception:
        pass
    return engine
