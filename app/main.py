from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, APIRouter, Response, Security, UploadFile, File, \
    Query, Form
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED

from app.utils import zipfile_generator, uploadFileValidation
from . import crud, models, schemas
from .database import SessionLocal, engine
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

apiKeyConfig = config.get('api-key', 'accesskey')

# API key setting
API_KEY = [apiKeyConfig]

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


# custom OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="FISH-AIR API",
        version="alpha 1.1.0",
        description="<h2>Getting Started</h2><p>This document introduced how to successfully call the Tulane Fish "
                    "Image and Metadata repository API to get multimedia metadata and associated metadata, "
                    "like Image Quality metadata. It assumes you are familiar with BGNN API and know how to perform "
                    "API calls.</p><p>The API key is a unique identifier that authenticates requests of calling the "
                    "API. Without a valid 'x-api-key' in request header, your request will not be processed. Please "
                    "contact Xiaojun Wang at <a href='xwang48@tulane.edu'>xwang48@tulane.edu</a> for a API key. "
                    "Please don't share your api key with others.</p> "
                    "<h3>API Version Alpha 1.1.0 </h3>"
                    "<h4>Updates</h4> <p>1. Convert folder structure to Fish-AIR_[Download Data Archive "
                    "ArkID]/Fish-AIR/Tulane/[Download Data Archive ArkID]/{data archive files}</p> "
        # "<h4>Improvements</h4> <p>New search parameters: Family, Genus, AI-Processed Data hierarchy </p>"
        ,
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
                "url": "https://bgnn.tulane.edu/terms/ImageQualityMetadata",
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


async def get_api_key(db: Session = Depends(get_db),
                      api_key_header: str = Security(api_key_header)
                      ):
    api_key_user = crud.get_people_by_apikey(db, api_key_header)
    if 'api_key' in api_key_user.keys():
        return api_key_user['api_key']
    else:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Token"
        )


@router.post("/create_your_key", tags=["Authorization"])
async def generate_api_key(firstName: str = Form(...), lastName: str = Form(...), email: str = Form(...),
                           purpose: str = Form(...), passcode: str = Form(...),
                           db: Session = Depends(get_db)):
    '''
        PUBLIC METHOD
        Create a new api key for yourself
        - param firstName: your first name
        - param lastName: your last_name
        - param email: your email
        - param purpose: what are you going to do with Fish-AIR dataset.
        - param passcode: A passcode using in workshop only for generate everybody's own api key
        - return: your own API KEY(Don't SHARE with others)
    '''
    if passcode != "Tu!TeMP1Key-workshop":
        raise HTTPException(
            status_code=404,
            detail="Wrong public passcode",
        )
    results = crud.create_people(db, first_name=firstName, last_name=lastName, email=email, purpose=purpose)
    if 'detail' in results.keys():
        raise HTTPException(
            status_code=400,
            detail=results["detail"]
        )
    return results


@router.post("/get_your_key", tags=["Authorization"])
async def get_apikey(email: str = Form(...), passcode: str = Form(...),
                     db: Session = Depends(get_db)):
    '''
        PUBLIC METHOD
        Get the api key you created
        - param email: your email
        - param passcode: A passcode  using in workshop only for generate everybody's own api key
        - return: your own API KEY(Don't SHARE with others)
    '''
    if passcode != "Tu!TeMP1Key-workshop":
        raise HTTPException(
            status_code=404,
            detail="Wrong passcode",
        )
    results = crud.get_people(db, email=email)
    if 'detail' in results.keys():
        raise HTTPException(
            status_code=400,
            detail=results["detail"]
        )
    return results


@router.get("/multimedias/", tags=["Multimedia"], response_model=List[schemas.MultimediaChild])
# async def read_multimedias(response: Response, genus: Optional[str] = None, dataset: schemas.DatasetName = schemas.DatasetName.glindataset, min_height: Optional[int] = None, max_height: Optional[int] = None, limit: Optional[int] = None, zipfile: bool = True,
async def read_multimedias(response: Response, api_key: str = Security(get_api_key), genus: Optional[str] = None,
                           family: Optional[str] = None, dataset: Optional[List[schemas.DatasetName]] = Query(None),
                           institution: Optional[str] = None,
                           maxWidth: Optional[int] = None, minWidth: Optional[int] = None,
                           maxHeight: Optional[int] = None,
                           minHeight: Optional[int] = None, batchARKID: Optional[str] = None, zipfile: bool = True,
                           db: Session = Depends(get_db)
                           ):
    '''
        PRIVATE METHOD
        get multimedias and associated (meta)data, like IQ, extended metadata, hirecachy medias
        - param genus: species genus
        - param family: species family
        - param institution: institution code
        - param dataset: dataset name(multiple selection)
        - param maxWidth: max width of image
        - param minWidth: min width of image
        - param maxHeight: max height of image
        - param minHeight: min height of image
        - param batchARKID: batch ARK ID
        - param zipfile: return JSON or Zip file
        - return: multimedia lists(with associated (meta)data). If zipfile is false, it will return 20 records(pagination will be added later)
    '''
    if dataset == schemas.DatasetName.none:
        dataset = None
    # multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, dataset=dataset,min_height=min_height,max_height=max_height, limit=limit)
    multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, family=family, dataset=dataset, zipfile=zipfile,
                                                     institution=institution,
                                                     max_width=maxWidth, max_height=maxHeight, min_width=minWidth,
                                                     min_height=minHeight,
                                                     batch_ark_id=batchARKID, limit=-1)
    if zipfile:
        # path, filename = zipfile_generator(multimedia_res, batch_res, params={"genus": genus, "dataset": dataset, "min_height": min_height, "max_height": max_height,"limit": limit})
        path, filename = zipfile_generator(multimedia_res, batch_res,
                                           params={"genus": genus, "family": family, "dataset": dataset})
        response.headers['X-filename'] = filename
        return FileResponse(path=path, filename=filename)
    return multimedia_res


@router.get("/multimedias_demo/", tags=["Multimedia"], response_model=List[schemas.MultimediaChild])
# async def read_multimedias(response: Response, genus: Optional[str] = None, dataset: schemas.DatasetName = schemas.DatasetName.glindataset, min_height: Optional[int] = None, max_height: Optional[int] = None, limit: Optional[int] = None, zipfile: bool = True,
async def read_multimedias(response: Response, genus: Optional[str] = None,
                           family: Optional[str] = None, dataset: Optional[List[schemas.DatasetName]] = Query(None),
                           institution: Optional[str] = None,
                           maxWidth: Optional[int] = None, minWidth: Optional[int] = None,
                           maxHeight: Optional[int] = None,
                           minHeight: Optional[int] = None, batchARKID: Optional[str] = None, zipfile: bool = True,
                           db: Session = Depends(get_db)
                           ):
    '''
        PUBLIC METHOD
        A demo for getting multimedias and associated (meta)data, like IQ, extended metadata, hirecachy medias
        - param genus: species genus
        - param family: species family
        - param institution: institution code
        - param dataset: dataset name(multiple selection)
        - param maxWidth: max width of image
        - param minWidth: min width of image
        - param maxHeight: max height of image
        - param minHeight: min height of image
        - param batchARKID: batch ARK ID
        - param zipfile: return JSON or Zip file
        - return: a list of 200 multimedias (with associated (meta)data). If zipfile is false, it will return 20 records
    '''
    if dataset == schemas.DatasetName.none:
        dataset = None
    # multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, dataset=dataset,min_height=min_height,max_height=max_height, limit=limit)
    multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, family=family, dataset=dataset, zipfile=zipfile,
                                                     institution=institution,
                                                     max_width=maxWidth, max_height=maxHeight, min_width=minWidth,
                                                     min_height=minHeight,
                                                     batch_ark_id=batchARKID, limit=200)
    if zipfile:
        # path, filename = zipfile_generator(multimedia_res, batch_res, params={"genus": genus, "dataset": dataset, "min_height": min_height, "max_height": max_height,"limit": limit})
        path, filename = zipfile_generator(multimedia_res, batch_res,
                                           params={"genus": genus, "family": family, "dataset": dataset})
        response.headers['X-filename'] = filename
        return FileResponse(path=path, filename=filename)
    return multimedia_res


@router.get("/multimedia_public/", tags=["Multimedia"], response_model=List[schemas.MultimediaChild])
# async def read_multimedias(response: Response, genus: Optional[str] = None, dataset: schemas.DatasetName = schemas.DatasetName.glindataset, min_height: Optional[int] = None, max_height: Optional[int] = None, limit: Optional[int] = None, zipfile: bool = True,
async def read_multimedias_public(response: Response, genus: Optional[str] = None, family: Optional[str] = None,
                                  dataset: schemas.DatasetName = schemas.DatasetName.glindataset, zipfile: bool = True,
                                  db: Session = Depends(get_db)
                                  ):
    '''
        PUBLIC METHOD - for students
        get multimedias and associated (meta)data, like IQ, extended metadata, hirecachy medias
        - param genus: species genus
        - param family: species family
        - param dataset: dataset name
        - param zipfile: return JSON or Zip file
        - return: multimedia lists(with associated (meta)data)
    '''
    # multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, dataset=dataset,min_height=min_height,max_height=max_height, limit=limit)
    multimedia_res, batch_res = crud.get_multimedia_public(db, genus=genus, family=family, dataset=dataset, limit=200,
                                                           zipfile=zipfile)
    if zipfile:
        # path, filename = zipfile_generator(multimedia_res, batch_res, params={"genus": genus, "dataset": dataset, "min_height": min_height, "max_height": max_height,"limit": limit})
        path, filename = zipfile_generator(multimedia_res, batch_res,
                                           params={"genus": genus, "family": family, "dataset": dataset})
        response.headers['X-filename'] = filename
        return FileResponse(path=path, filename=filename)
    return multimedia_res


@router.get("/multimedia/{ARKID}", tags=["Multimedia"], response_model=schemas.MultimediaChild)
async def read_multimedia_arkid(ARKID: str = 'qs243w0c', db: Session = Depends(get_db)):
    '''
        PUBLIC METHOD
         get multimedia and associated (meta)data, like IQ, extended metadata, hirecachy medias by ARK ID
    - param arkid: ark id (exp: qs243w0c)
    - return: multimedia entity
    '''
    iqs = crud.get_multimedia(db, ark_id=ARKID.strip())
    if iqs is None:
        raise HTTPException(status_code=404, detail="Image Not Found")
    return iqs


# @router.get("/iq/", tags=["Image Quality Metadata"], response_model=List[schemas.IQ])
# async def read_iqs(api_key: str = Security(get_api_key), skip: int = 0, limit: int = 100,
#                    db: Session = Depends(get_db)):
#     '''
#         PRIVATE METHOD
#         get image quality metadatas
#         - param skip: start index
#         - param limit: specify the number of records to return
#         - return: image quality metadata lists
#     '''
#     iqs = crud.get_iqs(db, skip=skip, limit=limit)
#     return iqs


@router.post("/batch/", tags=['Batch'], response_model=schemas.BatchMetadatum)
async def create_batch(api_key: str = Security(get_api_key),
                       institutionCode: str = Form(None),
                       batchName: str = Form(None),
                       pipeline: schemas.Pipeline = Form(None),
                       creatorComments: Optional[str] = Form(None),
                       codeRepository: Optional[str] = Form(None),
                       URL: Optional[str] = Form(None),
                       datasetName: str = Form("fish"),
                       bibliographicCitation: Optional[str] = Form(None),
                       supplementFile: Optional[UploadFile] = File(None, description="Upload supplement files"),
                       db: Session = Depends(get_db)):
    '''
        PRIVATE METHOD
        create a new batch
        - param institutionCode: Institution Code
        - param batchName: batch name
        - param pipeline: Source File/Bounding-Box/Segmentation/Landmark
        - param creator: creator name
        - param creatorComments: creator comment
        - param contactor: creator comment
        - param codeRepository: code repository
        - param URL: dataset/citation/website url
        - param datasetName: fish(default)/bird/etc..
        - param bibliographicCitation: citation info
        - param supplementFile: supplement file
        - return: New Batch
    '''
    batch = await crud.create_batch(db, institution=institutionCode, pipeline=pipeline, batchName=batchName,
                                    comment=creatorComments, codeRepo=codeRepository, url=URL,
                                    dataset=datasetName, citation=bibliographicCitation, supplement_file=supplementFile,
                                    api_key=api_key)
    if batch is None or isinstance(batch, str):
        raise HTTPException(status_code=404, detail="New batch creation failed. Please try again")
    return batch


@router.get("/batch/{batchARKID}", tags=['Batch'], response_model=schemas.BatchMetadatum)
async def get_batch(batchARKID: str, api_key: str = Security(get_api_key),
                    db: Session = Depends(get_db)):
    '''
        PRIVATE METHOD
        get batch by batch ark id
        - param institution: Institution Code
        - param pipeline: Source File/Bounding-Box/Segmentation/Landmark
        - param creator: creator name
        - param comment: creator comment
        - param codeRepo: code repository
        - param url: dataset/citation/website url
        - param dataset: fish(default)/bird/etc..
        - param citation: citation info
        - return: Batch lists
    '''
    batch = ""
    if batch is None or batch is str:
        raise HTTPException(status_code=404, detail="New batch creation failed. Please try again")
    # get batch if batch is none, otherwise return 404 and
    return batch


@router.get("/batch/", tags=['Batch'], response_model=List[schemas.BatchMetadatum])
async def get_batchlist(api_key: str = Security(get_api_key),
                        db: Session = Depends(get_db)):
    '''
        PRIVATE METHOD
        return all batches by user
        - return: Batches
    '''
    batches = crud.get_batch_list(db, api_key)
    if isinstance(batches, str):
        raise HTTPException(status_code=400, detail="Retrieve batches failed.")
    return batches


# upload image & metadata together
@router.post("/image/", tags=["Multimedia"])
async def upload_image(batchARKID: str = Form(...),
                       scientificName: str = Form(...),
                       genus: str = Form(...),
                       family: str = Form(...),
                       api_key: str = Security(get_api_key),
                       file: UploadFile = File(..., description="image file"),
                       parentARKID: str = Form(None),
                       license: str = Form(None),
                       source: str = Form(None),
                       ownerInstitutionCode: str = Form(None),
                       dataset: schemas.DatasetName = Form(None),
                       db: Session = Depends(get_db)):
    '''
        PRIVATE METHOD
        upload files streaming
        - param: Image File (size < 20mb, image type：JPEG/JPG/PNG/BMP/GIF)
        - param: batchARKID:
        - param: parentARKID:
        - param: license:
        - param: source:
        - param: ownerInstitutionCode:
        - param: scientificName:
        - param: genus:
        - param: family:
        - param: dataset: (segmentation/landmark/boundingbox)
        - return: upload success/failure and associate message
    '''
    image_validate_error = uploadFileValidation(file)
    if image_validate_error != '':
        raise HTTPException(status_code=400, detail=image_validate_error)
    new_multimedia = await crud.create_multimedia(
        db, file, batchARKID, parentARKID, license, source, ownerInstitutionCode,
        scientificName, genus, family, dataset)
    if isinstance(new_multimedia, str):
        raise HTTPException(status_code=400, detail=new_multimedia)
    return {
        'status': 'success',
        'ark_id': new_multimedia.ark_id
    }


# reupload image again if image has some issue.
# @router.post("/reUploadImage/", tags=["Upload"])
# async def re_upload_image(ark_id: str,
#                           file: UploadFile = File(..., description="file"),
#                           db: Session = Depends(get_db)):
#     '''
#         PRIVATE METHOD
#         upload files streaming
#         - param: Image File (size < 20mb, image type：JPEG/JPG/PNG/BMP/GIF)
#         - param: ark_id:
#         - return: upload success/failure and associate message:?
#     '''
#     image_validate_error = uploadFileValidation(file)
#     if image_validate_error != '':
#         raise HTTPException(status_code=400, detail=image_validate_error)
#     return 'reupload success'


app.include_router(router)
