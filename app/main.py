from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, APIRouter, Response, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.status import  HTTP_401_UNAUTHORIZED

from app.utils import zipfile_generator
from . import crud, models, schemas
from .database import SessionLocal, engine

# API key setting
API_KEY = ["Tu!TeMP1Key"]

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)



models.Base.metadata.create_all(bind=engine)
router = APIRouter()
app = FastAPI(
)

# configuration - CROS
origins = [
    "http://localhost",
    "http://localhost:8081",
    "http://192.168.13.158:8081",
    "http://192.168.0.5:8081"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

async def get_api_key(
    api_key_header: str = Security(api_key_header),
):

    if api_key_header in API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Token"
        )

# custom OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="BGNN API",
        version="alpha 1.0.0",
        description=" <h2>Getting Started</h2><p>This document introduced how to successfully call the Tulane Fish Image and Metadata repository API to get multimedia metadata and associated metadata, like Image Quality metadata. It assumes you are familiar with BGNN API and know how to perform API calls.</p><p>The API key is a unique identifier that authenticates requests of calling the API. Without a valid 'x-api-key' in request header, your request will not be processed. Please contact Xiaojun Wang at <a href='xwang48@tulane.edu'>xwang48@tulane.edu</a> for a API key. Please don't share your api key with others.</p>",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    tags_metadata = [
        {
            "name": "Multimedia",
            "description": "Multimedia information, the core of BGNN data repository ",
            "externalDocs": {
                "description": "Multimedia terms",
                "url": "https://bgnn.tulane.edu/terms/multimeida",
            },
        },
        {
            "name": "Image Quality Metadata",
            "description": "Quality Metadata for images",
            "externalDocs": {
                "description": "Image Quality terms",
                "url": "https://bgnn.tulane.edu/terms/multimeida",
            },
        },
    ]
    app.openapi_tags = tags_metadata
    return app.openapi_schema


app.openapi = custom_openapi


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# @app.post("/users/", response_model=schemas.User)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     db_user = crud.get_user_by_email(db, email=user.email)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return crud.create_user(db=db, user=user)
#
#
# @router.get("/users/", response_model=List[schemas.User])
# def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = crud.get_users(db, skip=skip, limit=limit)
#     return users
# #
# #
# @app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = crud.get_user(db, user_id=user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user
#
#
# @router.post("/users/{user_id}/items/", response_model=schemas.Item)
# def create_item_for_user(
#     user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
# ):
#     return crud.create_user_item(db=db, item=item, user_id=user_id)


# @app.get("/items/", response_model=List[schemas.Item])
# def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     items = crud.get_items(db, skip=skip, limit=limit)
#     return items



@router.get("/multimedias/", tags=["Multimedia"], response_model=List[schemas.MultimediaChild])
# async def read_multimedias(response: Response, genus: Optional[str] = None, dataset: schemas.DatasetName = schemas.DatasetName.glindataset, min_height: Optional[int] = None, max_height: Optional[int] = None, limit: Optional[int] = None, zipfile: bool = True,
async def read_multimedias(response: Response, api_key: str = Security(get_api_key), genus: Optional[str] = None, family: Optional[str] = None, dataset: schemas.DatasetName = schemas.DatasetName.glindataset, zipfile: bool = True,
                           db: Session = Depends(get_db)
                           ):
    '''
        PRIVATE METHOD
        get multimedias and associated (meta)data, like IQ, extended metadata, hirecachy medias
        - param genus: species genus
        - param family: species family
        - param dataset: dataset name
        - param zipfile: return JSON or Zip file
        - return: multimedia lists(with associated (meta)data)
    '''
    # multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, dataset=dataset,min_height=min_height,max_height=max_height, limit=limit)
    multimedia_res, batch_res = crud.get_multimedias(db, genus=genus,family=family, dataset=dataset, zipfile=zipfile)
    if zipfile:
        # path, filename = zipfile_generator(multimedia_res, batch_res, params={"genus": genus, "dataset": dataset, "min_height": min_height, "max_height": max_height,"limit": limit})
        path, filename = zipfile_generator(multimedia_res, batch_res, params={"genus": genus, "family": family,"dataset": dataset})
        response.headers['X-filename'] = filename
        return FileResponse(path=path, filename=filename)
    return multimedia_res

@router.get("/multimedia_public/", tags=["Multimedia"], response_model=List[schemas.MultimediaChild])
# async def read_multimedias(response: Response, genus: Optional[str] = None, dataset: schemas.DatasetName = schemas.DatasetName.glindataset, min_height: Optional[int] = None, max_height: Optional[int] = None, limit: Optional[int] = None, zipfile: bool = True,
async def read_multimedias(response: Response, genus: Optional[str] = None, family: Optional[str] = None, dataset: schemas.DatasetName = schemas.DatasetName.glindataset, zipfile: bool = True,
                           db: Session = Depends(get_db)
                           ):
    '''
        PUBLIC METHOD
        get multimedias and associated (meta)data, like IQ, extended metadata, hirecachy medias
        - param genus: species genus
        - param family: species family
        - param dataset: dataset name
        - param zipfile: return JSON or Zip file
        - return: multimedia lists(with associated (meta)data)
    '''
    # multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, dataset=dataset,min_height=min_height,max_height=max_height, limit=limit)
    multimedia_res, batch_res = crud.get_multimedia_public(db, genus=genus, family=family, dataset=dataset, limit=200, zipfile=zipfile)
    if zipfile:
        # path, filename = zipfile_generator(multimedia_res, batch_res, params={"genus": genus, "dataset": dataset, "min_height": min_height, "max_height": max_height,"limit": limit})
        path, filename = zipfile_generator(multimedia_res, batch_res, params={"genus": genus, "family": family,"dataset": dataset})
        response.headers['X-filename'] = filename
        return FileResponse(path=path, filename=filename)
    return multimedia_res


@router.get("/multimedia/{ark_id}", tags=["Multimedia"], response_model=schemas.MultimediaChild)
async def read_multimedia(ark_id: str = 'qs243w0c', db: Session = Depends(get_db)):
    '''
        PUBLIC METHOD
         get multimedia and associated (meta)data, like IQ, extended metadata, hirecachy medias by ARK ID
    - param arkid: ark id (exp: qs243w0c)
    - return: multimedia entity
    '''
    iqs = crud.get_multimedia(db, ark_id=ark_id.strip())
    if iqs is None:
        raise HTTPException(status_code=404, detail="Image Not Found")
    return iqs


@router.get("/iq/", tags=["Image Quality Metadata"], response_model=List[schemas.IQ])
async def read_iqs(api_key: str = Security(get_api_key), skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    '''
        PRIVATE METHOD
        get image quality metadatas
        - param skip: start index
        - param limit: specify the number of records to return
        - return: image quality metadata lists
    '''
    iqs = crud.get_iqs(db, skip=skip, limit=limit)
    return iqs


app.include_router(router)
