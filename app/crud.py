import io
import json
import uuid

from fastapi import UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.utils import minter
import app.config as config
from PIL import Image

from . import model_text

# def get_user(db: Session, user_id: int):
#     return db.query(models.User).filter(models.User.id == user_id).first()
#
#
# def get_user_by_email(db: Session, email: str):
#     return db.query(models.User).filter(models.User.email == email).first()
#
#
# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     return (
#         db.query(models.User)
#         .order_by(models.User.id)
#         .offset(skip)
#         .limit(limit)
#         .all()
#     )
#
#
# def create_user(db: Session, user: schemas.UserCreate):
#     fake_hashed_password = user.password + "notreallyhashed"
#     db_user = models.User(
#         email=user.email, hashed_password=fake_hashed_password
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user
#
#
# def get_items(db: Session, skip: int = 0, limit: int = 100):
#     return (
#         db.query(models.Item)
#         .order_by(models.Item.id)
#         .offset(skip)
#         .limit(limit)
#         .all()
#     )
#
#
# def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
#     db_item = models.Item(**item.dict(), owner_id=user_id)
#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)
#     return db_item


def get_iqs(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(model_text.ImageQualityMetadatum)
        .offset(skip)
        .limit(limit)
        .all()
    )

#Batches
def create_batch(db:Session,institution, pipeline,
                       creator, comment, codeRepo, url,
                       dataset, citation):
    ark_id_obj = minter(config.ARK_BATCH)
    new_batch = model_text.Batch(ark_id=ark_id_obj[2])
    new_batch.institution_code = institution
    new_batch.pipeline = pipeline
    new_batch.creator = creator
    new_batch.creator_comment = comment
    new_batch.code_repository = codeRepo
    new_batch.url = url
    new_batch.identifier = ark_id_obj[0] + ':/' + ark_id_obj[1] + '/' + ark_id_obj[2]
    new_batch.dataset_name = dataset
    new_batch.bibliographic_citation = citation
    try:
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)
        return new_batch
    except Exception as error:
        db.rollback()
        return str(error)

#new multimedia
def create_multimedia(db: Session, file: UploadFile, batch_ark_id, prarent_ark_id, image_license, image_source, image_institution_code,
                      scientific_name,genus, family, dataset):
    #get information from upload image

    # 打开图像文件
    image_content = file.file
    image = Image.open(image_content)
    # 获取图像宽度和高度
    width, height = image.size
    #insert media
    multimedia_ark_id_obj = minter(config.ARK_MULTIMEDIA)
    new_multimedia = model_text.Multimeida(ark_id=multimedia_ark_id_obj[2],parent_ark_id=prarent_ark_id)
    new_multimedia.parent_ark_id = prarent_ark_id
    new_multimedia.batch_ark_id = batch_ark_id
    matched_batch = db.query(model_text.Batch).filter(model_text.Batch.ark_id == batch_ark_id).all()
    if matched_batch is not None:
        new_multimedia.batch_id = matched_batch[0].batch_name
    new_multimedia.filename_as_delivered = file.filename
    new_multimedia.format = file.filename.split(".")[1]
    new_multimedia.path = "https://bgnn.tulane.edu/hdr-share/ark/89609/" + multimedia_ark_id_obj[2] + "." + new_multimedia.format

    new_multimedia.license = image_license
    new_multimedia.source = image_source
    new_multimedia.owner_institution_code = image_institution_code

    new_multimedia.scientific_name = scientific_name
    new_multimedia.genus = genus
    new_multimedia.family = family
    new_multimedia.dataset = dataset

    new_mul_extendMetadata = model_text.ExtendedImageMetadatum(ark_id=new_multimedia.ark_id, ext_image_metadata_id=str(uuid.uuid4()))
    new_mul_extendMetadata.license = 'CC BY-NC'
    new_mul_extendMetadata.publisher = 'Fish-Air'
    new_mul_extendMetadata.owner_institution_code = 'TUBRI'
    new_mul_extendMetadata.width = width
    new_mul_extendMetadata.height = height
    new_mul_extendMetadata.size = len(file.file.read())

    try:
        db.add(new_multimedia)
        db.add(new_mul_extendMetadata)
        db.commit()
        db.refresh(new_multimedia)
        db.refresh(new_mul_extendMetadata)

        return new_multimedia
    except Exception as error:
        db.rollback()
        return str(error)


# def get_multimedias(db: Session, genus, dataset, max_height, min_height, limit: int = 200 ):
def get_multimedias(db: Session, genus, family, dataset, institution, max_width, min_width,max_height, min_height, batch_ark_id,zipfile):
    if genus is None:
        genus = ''
    if family is None:
        family = ''
    if institution is None:
        institution= ''
    if batch_ark_id is None:
        batch_ark_id = ''
    if min_height is None:
        min_height = -1
    if max_height is None:
        max_height = -1
    if min_width is None:
        min_width = -1
    if max_width is None:
        max_width = -1
    if zipfile is False:
         multimedia_results = db.query(model_text.Multimeida). \
            join(model_text.ExtendedImageMetadatum). \
            filter(
            or_(genus == '', model_text.Multimeida.genus.ilike('%' + genus + '%')),
            or_(family == '', model_text.Multimeida.family.ilike('%' + family + '%')),
            or_(model_text.Multimeida.dataset.in_(dataset), dataset == None),
            or_(institution == '', model_text.Multimeida.owner_institution_code == institution),
            or_(batch_ark_id == '', model_text.Multimeida.batch_ark_id == batch_ark_id),
            # model_text.Multimeida.owner_institution_code == 'INHS',
            # model_text.Multimeida.owner_institution_code == 'FMNH',
            # model_text.Multimeida.owner_institution_code == 'OSUM',
            # model_text.Multimeida.owner_institution_code == 'UMMZ',
            #or_(filesize is None, model_text.ExtendedImageMetadatum.height >= min_height ),
            or_(min_height == -1, model_text.ExtendedImageMetadatum.height >= min_height ),
            or_( max_height == -1, model_text.ExtendedImageMetadatum.height <= max_height),
             or_(min_width == -1, model_text.ExtendedImageMetadatum.width >= min_width),
             or_(max_width == -1, model_text.ExtendedImageMetadatum.width <= max_width)
            # or_(model_text.Multimeida.owner_institution_code == 'INHS', institution== None),
        ).options(joinedload(model_text.Multimeida.extended_metadata),
                  joinedload(model_text.Multimeida.quality_metadata),
                  joinedload(model_text.Multimeida.batch)) \
            .limit(20).subquery()
    else:
        multimedia_results = db.query(model_text.Multimeida).\
            join(model_text.ExtendedImageMetadatum).\
            filter(
            or_(genus == '', model_text.Multimeida.genus.ilike('%' + genus + '%')),
            or_(family == '', model_text.Multimeida.family.ilike('%' + family + '%')),
            or_(model_text.Multimeida.dataset.in_(dataset), dataset == None),
            or_(institution == '', model_text.Multimeida.owner_institution_code == institution),
            or_(batch_ark_id == '', model_text.Multimeida.batch_ark_id == batch_ark_id),
            # model_text.Multimeida.owner_institution_code == 'INHS',
            # model_text.Multimeida.owner_institution_code == 'FMNH',
            # model_text.Multimeida.owner_institution_code == 'OSUM',
            # model_text.Multimeida.owner_institution_code == 'UMMZ',
            # or_(filesize is None, model_text.ExtendedImageMetadatum.height >= min_height ),
            or_(min_height == -1, model_text.ExtendedImageMetadatum.height >= min_height),
            or_(max_height == -1, model_text.ExtendedImageMetadatum.height <= max_height),
            or_(min_width == -1, model_text.ExtendedImageMetadatum.width >= min_width),
            or_(max_width == -1, model_text.ExtendedImageMetadatum.width <= max_width)
            # or_(model_text.Multimeida.owner_institution_code == 'INHS', institution== None),
        ).options(joinedload(model_text.Multimeida.extended_metadata),
                  joinedload(model_text.Multimeida.quality_metadata),
                  joinedload(model_text.Multimeida.batch)) \
            .subquery()
    # batch_results = db.query(model_text.Batch).join(model_text.Multimeida).filter(
    #     model_text.Multimeida.genus.ilike('%' + genus + '%'),
    #     model_text.Multimeida.family.ilike('%' + family + '%'),
    #     or_(model_text.Multimeida.dataset == dataset, dataset == None)).all()
    batch_results = db.query(model_text.Batch).filter(model_text.Batch.ark_id == multimedia_results.c.batch_ark_id).all()
    multimedia_results = db.query(model_text.Multimeida).select_entity_from(multimedia_results).all()
    return multimedia_results, batch_results

# for public
def get_multimedia_public(db: Session, genus, family, dataset, zipfile, limit: int = 200):
    if genus is None:
        genus = ''
    if family is None:
        family = ''
    if zipfile is False:
         multimedia_results = db.query(model_text.Multimeida). \
            join(model_text.ExtendedImageMetadatum). \
            filter(
            or_(genus == '', model_text.Multimeida.genus.ilike('%' + genus + '%')),
            or_(family == '', model_text.Multimeida.family.ilike('%' + family + '%')),
            or_(model_text.Multimeida.dataset == dataset, dataset == None),
            # model_text.Multimeida.owner_institution_code == 'INHS',
            # model_text.Multimeida.owner_institution_code == 'FMNH',
            # model_text.Multimeida.owner_institution_code == 'OSUM',
            # model_text.Multimeida.owner_institution_code == 'UMMZ',
            # or_(min_height is None, model_text.ExtendedImageMetadatum.height >= min_height ),
            # or_( max_height is None, model_text.ExtendedImageMetadatum.height <= max_height)
            # or_(model_text.Multimeida.owner_institution_code == 'INHS', institution== None),
        ).options(joinedload(model_text.Multimeida.extended_metadata),
                  joinedload(model_text.Multimeida.quality_metadata),
                  joinedload(model_text.Multimeida.batch)) \
            .limit(20).all()
    else:
        multimedia_results = db.query(model_text.Multimeida).\
            join(model_text.ExtendedImageMetadatum).\
            filter(
            or_(genus == '', model_text.Multimeida.genus.ilike('%' + genus + '%')),
            or_(family == '', model_text.Multimeida.family.ilike('%' + family + '%')),
            or_(model_text.Multimeida.dataset == dataset, dataset == None),
            # model_text.Multimeida.owner_institution_code == 'INHS',
            # model_text.Multimeida.owner_institution_code == 'FMNH',
            # model_text.Multimeida.owner_institution_code == 'OSUM',
            # model_text.Multimeida.owner_institution_code == 'UMMZ',
            # or_(min_height is None, model_text.ExtendedImageMetadatum.height >= min_height ),
            # or_( max_height is None, model_text.ExtendedImageMetadatum.height <= max_height)
            # or_(model_text.Multimeida.owner_institution_code == 'INHS', institution== None),
        ).options(joinedload(model_text.Multimeida.extended_metadata),
                 joinedload(model_text.Multimeida.quality_metadata),
                 joinedload(model_text.Multimeida.batch))\
            .limit(limit).all()
    batch_results = db.query(model_text.Batch).join(model_text.Multimeida).filter(
        model_text.Multimeida.genus.ilike('%' + genus + '%'),
        model_text.Multimeida.family.ilike('%' + family + '%'),
        or_(model_text.Multimeida.dataset == dataset, dataset == None)).all()
    return multimedia_results, batch_results


def get_multimedia(db: Session, ark_id):
    results = db.query(model_text.Multimeida)\
        .filter(
        model_text.Multimeida.ark_id == ark_id)\
        .options(joinedload(model_text.Multimeida.extended_metadata),
             joinedload(model_text.Multimeida.quality_metadata))\
        .all()
    if len(results) > 0:
        return(results[0])
    else:
        return None
