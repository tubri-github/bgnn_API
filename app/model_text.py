# coding: utf-8
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Batch(Base):
    __tablename__ = 'batch'

    batch_id = Column(String, primary_key=True)
    batch_name = Column(String)
    institution_code = Column(String)
    pipeline = Column(String)
    create_date = Column(Time(True))
    update_date = Column(Time(True))
    uploader_id = Column(String)
    citation = Column(String)


class Multimeida(Base):
    __tablename__ = 'multimeida'

    ark_id = Column(String, primary_key=True)
    parent_ark_id = Column(String)
    batch_id = Column(String)
    path = Column(String)
    filename_as_delivered = Column(String)
    format = Column(String)
    create_date = Column(Time(True))
    modify_date = Column(Time(True))
    license = Column(String)
    source = Column(String)
    owner_institution_code = Column(String)

    extended_metadata = relationship("ExtendedImageMetadatum", back_populates="ark")


class Person(Base):
    __tablename__ = 'people'

    people_id = Column(String, primary_key=True)
    email = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    create_time = Column(Time(True))
    update_time = Column(Time(True))
    last_login = Column(Time(True))
    lab = Column(String)
    supervisor_id = Column(String)


class ExtendedImageMetadatum(Base):
    __tablename__ = 'extended_image_metadata'

    ext_image_metadata_id = Column(String, primary_key=True)
    ark_id = Column(ForeignKey('multimeida.ark_id'), nullable=False)
    create_date = Column(Time(True))
    metadata_date = Column(Time(True))
    size = Column(BigInteger)
    width = Column(BigInteger)
    height = Column(BigInteger)
    license = Column(String)
    publisher = Column(String)
    owner_institution_code = Column(String)
    resolution = Column(String)

    ark = relationship('Multimeida', back_populates="extended_metadata")


class ImageQualityMetadatum(Base):
    __tablename__ = 'image_quality_metadata'

    iq_metadata_id = Column(String, primary_key=True)
    ark_id = Column(ForeignKey('multimeida.ark_id'), nullable=False)
    specimen_quantity = Column(Integer)
    non_specimen_objects = Column(String)
    contains_scalebar = Column(Boolean)
    contains_colorbar = Column(Boolean)
    contains_barcode = Column(Boolean)
    contains_label = Column(Boolean)
    brightness = Column(String)
    color_issue = Column(String)
    parts_folded = Column(Boolean)
    parts_missing = Column(Boolean)
    parts_overlapping = Column(Boolean)
    all_parts_visible = Column(Boolean)
    specimen_angle = Column(String)
    specimen_view = Column(String)
    specimen_curved = Column(String)
    uniform_background = Column(Boolean)
    on_focus = Column(Boolean)
    quality = Column(Integer)
    accession_number_validity = Column(Boolean)
    creator_id = Column(ForeignKey('people.people_id'))
    data_capture_method = Column(String)
    reviewer_id = Column(String)
    license = Column(String)
    publisher = Column(String)
    owner_institution_code = Column(String)
    create_date = Column(String(10))
    metadata_date = Column(String(10))

    ark = relationship('Multimeida')
    creator = relationship('Person')
