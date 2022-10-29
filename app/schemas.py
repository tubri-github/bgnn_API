from datetime import time
from typing import List, Optional

from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []

    class Config:
        orm_mode = True


##IQ##
class IQBase(BaseModel):
    # ark_id: str
    specimen_quantity: int
    non_specimen_objects = str
    contains_scalebar: bool
    contains_colorbar: bool
    contains_barcode: bool
    contains_label: bool
    brightness: str
    color_issue: str
    parts_folded: bool
    parts_missing: bool
    parts_overlapping: bool
    all_parts_visible: bool
    specimen_angle: str
    specimen_view: str
    specimen_curved: str
    uniform_background: bool
    on_focus: bool
    quality: int
    accession_number_validity: bool
    data_capture_method: str
    license: str
    publisher: str
    owner_institution_code: str
    create_date: str
    metadata_date: str


class IQ(IQBase):
    iq_metadata_id: str

    class Config:
        orm_mode = True


##Extended image metadata
class ExtendedImageBase(BaseModel):
    create_date = time
    metadata_date = time
    size: int
    width: int
    height: int
    license: str
    publisher: str
    owner_institution_code: str
    resolution: Optional[str]


class ExtendedImageMetadatum(ExtendedImageBase):
    ext_image_metadata_id: str

    class Config:
        orm_mode = True


##Multimedia##
class MultimediaBase(BaseModel):
    path: str
    filename_as_delivered: str
    format: str
    create_date = time
    modify_date = time
    license: str
    source: str
    owner_institution_code: str
    scientific_name: str
    genus: str
    family: str


##Batch
class BatchBase(BaseModel):
    batch_name: str
    institution_code: str
    pipeline: str
    # create_date: time
    # modify_date: time
    creator_comment: str
    contactor: str
    lab_code: str
    project_name: str
    url: str
    identifier: str
    dataset_name: str
    bibliographic_citation: str
    creator: str


class BatchMetadatum(BatchBase):
    ark_id: str

    class Config:
        orm_mode = True


class Multimedia(MultimediaBase):
    ark_id: str
    parent_ark_id: str
    batch_id: str
    children: List['Multimedia'] = []

    class Config:
        orm_mode = True


class MultimediaExtended(Multimedia):
    extended_metadata: List[ExtendedImageMetadatum]
    quality_metadata: List[IQ]
    batch: BatchMetadatum


class MultimediaChild(MultimediaExtended):
    parent: Optional['MultimediaChild']


Multimedia.update_forward_refs()
