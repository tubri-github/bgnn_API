"""
CURD parts
!!!This section of code needs to be refactored and remove redundant parts.
"""
import os
import uuid

import aiofiles
from fastapi import UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.utils import minter, create_api_key
import app.config as config
from PIL import Image
from pathlib import Path

from . import model_text


def get_iqs(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(model_text.ImageQualityMetadatum)
        .offset(skip)
        .limit(limit)
        .all()
    )


# Person
def create_people(db: Session, first_name, last_name,
                  email, purpose):
    user = db.query(model_text.Person).filter(model_text.Person.email == email).first()
    if user:
        return {'detail': 'Email already exists'}
    api_key = create_api_key()
    user_id = str(uuid.uuid4())
    user = model_text.Person(people_id=user_id, first_name=first_name, last_name=last_name, email=email,
                             purpose=purpose, api_key=api_key)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"api_key": api_key}


def get_people(db: Session, email):
    user = db.query(model_text.Person).filter(model_text.Person.email == email).first()
    if not user:
        return {'detail': 'Email Not Found'}
    api_key = user.api_key
    return {"email": user.email, "api_key": api_key}


def get_people_by_apikey(db: Session, api_key):
    user = db.query(model_text.Person).filter(model_text.Person.api_key == api_key).first()
    if not user:
        return {'detail': 'API Key not valid'}
    api_key = user.api_key
    return {"api_key": api_key}


# Batches
async def create_batch(db: Session, institution, pipeline,
                       comment, codeRepo, url,
                       dataset, citation, supplement_file, api_key):
    try:
        user = db.query(model_text.Person).filter(model_text.Person.api_key == api_key).first()
        if not user:
            return {'detail': 'API Key not valid'}
        creator_id = user.people_id
        creator_name = user.first_name + ' ' + user.last_name
        ark_id_obj = minter(config.ARK_BATCH)
        path = Path("/www/hdr/hdr-share/ftp/ark/89609/" + ark_id_obj[2] + "/supplement_file/")
        if not os.path.exists(path):
            os.makedirs(path)
        if supplement_file is not None:
            file_name = Path(path, supplement_file.filename)
            if not os.path.exists(file_name):
                async with aiofiles.open(file_name, 'wb') as f:
                    await f.write(supplement_file.file.read())

    except Exception as error:
        return str("upload supplement failed:" + str(error))

    new_batch = model_text.Batch(ark_id=ark_id_obj[2])
    new_batch.institution_code = institution
    new_batch.pipeline = pipeline
    new_batch.creator = creator_name
    new_batch.creator_user_id = creator_id
    new_batch.creator_comment = comment
    new_batch.code_repository = codeRepo
    new_batch.url = url
    new_batch.identifier = ark_id_obj[0] + '/' + ark_id_obj[1] + '/' + ark_id_obj[2]
    new_batch.dataset_name = dataset
    new_batch.bibliographic_citation = citation
    if supplement_file is not None:
        new_batch.supplement_path = "https://fishair.org/hdr-share/ftp/ark/89609/" + ark_id_obj[
            2] + "/supplement_file/" + supplement_file.filename
    try:
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)
        return new_batch
    except Exception as error:
        db.rollback()
        return str(error)


# return batchlist by user apikey
def get_batch_list(db: Session, api_key):
    user = db.query(model_text.Person).filter(model_text.Person.api_key == api_key).first()
    if user is None:
        return "Invalid API key or User doesn't exist."
    batch_list = db.query(model_text.Batch).filter(model_text.Batch.creator_user_id == user.people_id).all()
    return batch_list


# new multimedia
async def create_multimedia(db: Session, file: UploadFile, batch_ark_id, prarent_ark_id, image_license, image_source,
                            image_institution_code,
                            scientific_name, genus, family, dataset):
    # check if batch arkid exists
    matched_batch = db.query(model_text.Batch).filter(model_text.Batch.ark_id == batch_ark_id).all()
    if len(matched_batch) == 0:
        return "Sorry, there is no matched batch ARK ID."
    try:
        # get information from upload image

        # open image from UploadFile
        image_content = file.file
        image = Image.open(image_content)
        # get image width and height
        width, height = image.size
        # turn the file pointer from the end of the file to the start of the file
        file.file.seek(0)

        # insert media
        multimedia_ark_id_obj = minter(config.ARK_MULTIMEDIA)

        path = Path("c:\\" + batch_ark_id)
        if not os.path.exists(path):
            os.makedirs(path)
        file_name = Path(path, multimedia_ark_id_obj[2] + '.' + file.filename.split(".")[1])
        if not os.path.exists(file_name):
            async with aiofiles.open(file_name, 'wb') as f:
                await f.write(file.file.read())
    except Exception as error:
        return str(error)
    new_multimedia = model_text.Multimeida(ark_id=multimedia_ark_id_obj[2], parent_ark_id=prarent_ark_id)
    new_multimedia.parent_ark_id = prarent_ark_id
    new_multimedia.batch_ark_id = batch_ark_id
    new_multimedia.batch_id = matched_batch[0].batch_name
    new_multimedia.filename_as_delivered = file.filename
    new_multimedia.format = file.filename.split(".")[1]
    new_multimedia.path = "https://fishair.org/hdr-share/ftp/ark/89609/" + batch_ark_id + "/" + multimedia_ark_id_obj[
        2] + "." + new_multimedia.format

    new_multimedia.license = image_license
    new_multimedia.source = image_source
    new_multimedia.owner_institution_code = image_institution_code

    new_multimedia.scientific_name = scientific_name
    new_multimedia.genus = genus
    new_multimedia.family = family
    new_multimedia.dataset = dataset

    new_mul_extendMetadata = model_text.ExtendedImageMetadatum(ark_id=new_multimedia.ark_id,
                                                               ext_image_metadata_id=str(uuid.uuid4()))
    new_mul_extendMetadata.license = 'CC BY-NC'
    new_mul_extendMetadata.publisher = 'Fish-Air'
    new_mul_extendMetadata.owner_institution_code = 'TUBRI'
    new_mul_extendMetadata.width = width
    new_mul_extendMetadata.height = height
    # turn the file pointer from the end of the file to the start of the file
    file.file.seek(0)
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


def get_multimedias(db: Session, genus, family, dataset, institution, max_width, min_width, max_height, min_height,
                    batch_ark_id, zipfile, limit):
    if genus is None:
        genus = ''
    if family is None:
        family = ''
    if institution is None:
        institution = ''
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
            or_(institution == '', model_text.Multimeida.owner_institution_code == institution),
            or_(batch_ark_id == '', model_text.Multimeida.batch_ark_id == batch_ark_id),
            or_(min_height == -1, model_text.ExtendedImageMetadatum.height >= min_height),
            or_(max_height == -1, model_text.ExtendedImageMetadatum.height <= max_height),
            or_(min_width == -1, model_text.ExtendedImageMetadatum.width >= min_width),
            or_(max_width == -1, model_text.ExtendedImageMetadatum.width <= max_width)
        ).options(joinedload(model_text.Multimeida.extended_metadata),
                  joinedload(model_text.Multimeida.quality_metadata),
                  joinedload(model_text.Multimeida.batch)) \
            .order_by(model_text.Multimeida.ark_id).limit(20).subquery()
    else:
        multimedia_results = db.query(model_text.Multimeida). \
            join(model_text.ExtendedImageMetadatum). \
            filter(
            or_(genus == '', model_text.Multimeida.genus.ilike('%' + genus + '%')),
            or_(family == '', model_text.Multimeida.family.ilike('%' + family + '%')),
            # or_(model_text.Multimeida.dataset.in_(dataset), dataset == None),
            or_(institution == '', model_text.Multimeida.owner_institution_code == institution),
            or_(batch_ark_id == '', model_text.Multimeida.batch_ark_id == batch_ark_id),
            or_(min_height == -1, model_text.ExtendedImageMetadatum.height >= min_height),
            or_(max_height == -1, model_text.ExtendedImageMetadatum.height <= max_height),
            or_(min_width == -1, model_text.ExtendedImageMetadatum.width >= min_width),
            or_(max_width == -1, model_text.ExtendedImageMetadatum.width <= max_width)
        ).options(joinedload(model_text.Multimeida.extended_metadata),
                  joinedload(model_text.Multimeida.quality_metadata),
                  joinedload(model_text.Multimeida.batch)) \
            .subquery()
    batch_results = db.query(model_text.Batch).filter(
        model_text.Batch.ark_id == multimedia_results.c.batch_ark_id).all()
    if limit == -1:
        if dataset is not None:
            multimedia_results = db.query(model_text.Multimeida).select_entity_from(multimedia_results).filter(
                model_text.Multimeida.dataset.in_(dataset)).all()
        else:
            multimedia_results = db.query(model_text.Multimeida).select_entity_from(multimedia_results).all()

    else:
        if dataset is not None:
            multimedia_results = db.query(model_text.Multimeida).select_entity_from(multimedia_results).filter(
                model_text.Multimeida.dataset.in_(dataset)).order_by(model_text.Multimeida.ark_id).limit(limit).all()
        else:
            multimedia_results = db.query(model_text.Multimeida).select_entity_from(multimedia_results).order_by(
                model_text.Multimeida.ark_id).limit(limit).all()
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
        ).options(joinedload(model_text.Multimeida.extended_metadata),
                  joinedload(model_text.Multimeida.quality_metadata),
                  joinedload(model_text.Multimeida.batch)) \
            .limit(20).all()
    else:
        multimedia_results = db.query(model_text.Multimeida). \
            join(model_text.ExtendedImageMetadatum). \
            filter(
            or_(genus == '', model_text.Multimeida.genus.ilike('%' + genus + '%')),
            or_(family == '', model_text.Multimeida.family.ilike('%' + family + '%')),
            or_(model_text.Multimeida.dataset == dataset, dataset == None),
        ).options(joinedload(model_text.Multimeida.extended_metadata),
                  joinedload(model_text.Multimeida.quality_metadata),
                  joinedload(model_text.Multimeida.batch)) \
            .limit(limit).all()
    batch_results = db.query(model_text.Batch).join(model_text.Multimeida).filter(
        model_text.Multimeida.genus.ilike('%' + genus + '%'),
        model_text.Multimeida.family.ilike('%' + family + '%'),
        or_(model_text.Multimeida.dataset == dataset, dataset == None)).all()
    return multimedia_results, batch_results


def get_multimedia(db: Session, ark_id):
    results = db.query(model_text.Multimeida) \
        .filter(
        model_text.Multimeida.ark_id == ark_id) \
        .options(joinedload(model_text.Multimeida.extended_metadata),
                 joinedload(model_text.Multimeida.quality_metadata)) \
        .all()
    if len(results) > 0:
        return (results[0])
    else:
        return None
