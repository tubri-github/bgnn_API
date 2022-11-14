import json

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from . import models, schemas, model_text


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


def get_multimedias(db: Session, genus, dataset, max_height: int = 6500, min_height: int = 0, skip: int = 0, limit: int = 200, ):
    multimedia_results = db.query(model_text.Multimeida).\
        join(model_text.ExtendedImageMetadatum).\
        filter(
        model_text.Multimeida.genus.ilike('%' + genus + '%'),
        model_text.Multimeida.owner_institution_code == dataset,
        model_text.ExtendedImageMetadatum.height >= min_height,
        model_text.ExtendedImageMetadatum.height <= max_height
        # or_(model_text.Multimeida.owner_institution_code == 'INHS', institution== None),
    ).options(joinedload(model_text.Multimeida.extended_metadata),
             joinedload(model_text.Multimeida.quality_metadata),
             joinedload(model_text.Multimeida.batch)).offset(skip)\
        .limit(limit)\
        .all()
    batch_results = db.query(model_text.Batch).join(model_text.Multimeida).filter(model_text.Multimeida.genus.ilike('%' + genus + '%'),
                                                      model_text.Multimeida.owner_institution_code == dataset).all()
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
