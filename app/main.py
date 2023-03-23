import hashlib
from typing import List, Optional

import base64
import os
import re
import shutil
import stat
from email.utils import formatdate
from mimetypes import guess_type
from pathlib import Path
from urllib.parse import quote

import aiofiles

from fastapi import Depends, FastAPI, HTTPException, APIRouter, Response, Security, Request, Body, UploadFile, File, \
    Path as F_Path, Query, Form
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.responses import StreamingResponse

from app.utils import zipfile_generator, uploadFileValidation
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
@router.post("/create_your_key")
async def generate_api_key(firstName:str = Form(...),lastName:str = Form(...), email:str=Form(...), purpose: str = Form(...),passcode: str = Form(...),
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
    results = crud.create_people(db, first_name=firstName, last_name= lastName, email=email, purpose=purpose)
    if 'detail' in results.keys():
        raise HTTPException(
            status_code=400,
            detail=results["detail"]
        )
    return results

@router.post("/get_your_key")
async def get_apikey(email:str=Form(...), passcode: str = Form(...),
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
                           family: Optional[str] = None, dataset: Optional[List[schemas.DatasetName]] = Query(None), institution: Optional[str] = None,
                           maxWidth: Optional[int] = None, minWidth: Optional[int] = None ,maxHeight: Optional[int] = None,
                           minHeight: Optional[int] = None, batchARKID: Optional[str] = None,zipfile: bool = True,
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
    multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, family=family, dataset=dataset, zipfile=zipfile,institution=institution,
                                                    max_width=maxWidth,max_height=maxHeight,min_width=minWidth,min_height=minHeight,
                                                     batch_ark_id=batchARKID,limit=-1)
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
                           family: Optional[str] = None, dataset: Optional[List[schemas.DatasetName]] = Query(None), institution: Optional[str] = None,
                           maxWidth: Optional[int] = None, minWidth: Optional[int] = None ,maxHeight: Optional[int] = None,
                           minHeight: Optional[int] = None, batchARKID: Optional[str] = None,zipfile: bool = True,
                           db: Session = Depends(get_db)
                           ):
    '''
        PUBLIC METHOD
        A demo for getting multimedias and associated (meta)data, like IQ, extended metadata, hirecachy medias
        - param genus: species genus
        - param family: species family
        - param institution: institution code
        - param dataset: dataset name(multiple selection)
        - param max_width: max width of image
        - param min_width: min width of image
        - param max_height: max height of image
        - param min_height: min height of image
        - param batch_ark_id: batch ARK ID
        - param zipfile: return JSON or Zip file
        - return: a list of 200 multimedias (with associated (meta)data). If zipfile is false, it will return 20 records
    '''
    if dataset == schemas.DatasetName.none:
        dataset = None
    # multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, dataset=dataset,min_height=min_height,max_height=max_height, limit=limit)
    multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, family=family, dataset=dataset, zipfile=zipfile,institution=institution,
                                                    max_width=maxWidth,max_height=maxHeight,min_width=minWidth,min_height=minHeight,
                                                     batch_ark_id=batchARKID,limit=200)
    if zipfile:
        # path, filename = zipfile_generator(multimedia_res, batch_res, params={"genus": genus, "dataset": dataset, "min_height": min_height, "max_height": max_height,"limit": limit})
        path, filename = zipfile_generator(multimedia_res, batch_res,
                                           params={"genus": genus, "family": family, "dataset": dataset})
        response.headers['X-filename'] = filename
        return FileResponse(path=path, filename=filename)
    return multimedia_res

@router.put("/multimedias/", tags=["Multimedia"])
# async def read_multimedias(response: Response, genus: Optional[str] = None, dataset: schemas.DatasetName = schemas.DatasetName.glindataset, min_height: Optional[int] = None, max_height: Optional[int] = None, limit: Optional[int] = None, zipfile: bool = True,
async def update_multimedias(response: Response, ark_id: str, api_key: str = Security(get_api_key),
                             db: Session = Depends(get_db)
                             ):
    '''
        PRIVATE METHOD
        update multimedias and associated (meta)data, like IQ, extended metadata, hirecachy medias
        - param ark_id: ark id
        - return: updated multimedia
    '''
    # multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, dataset=dataset,min_height=min_height,max_height=max_height, limit=limit)

    return "1"


@router.get("/multimedia_public/", tags=["Multimedia"], response_model=List[schemas.MultimediaChild])
# async def read_multimedias(response: Response, genus: Optional[str] = None, dataset: schemas.DatasetName = schemas.DatasetName.glindataset, min_height: Optional[int] = None, max_height: Optional[int] = None, limit: Optional[int] = None, zipfile: bool = True,
async def read_multimedias_public(response: Response, genus: Optional[str] = None, family: Optional[str] = None,
                                  dataset: schemas.DatasetName = schemas.DatasetName.glindataset, zipfile: bool = True,
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
    multimedia_res, batch_res = crud.get_multimedia_public(db, genus=genus, family=family, dataset=dataset, limit=200,
                                                           zipfile=zipfile)
    if zipfile:
        # path, filename = zipfile_generator(multimedia_res, batch_res, params={"genus": genus, "dataset": dataset, "min_height": min_height, "max_height": max_height,"limit": limit})
        path, filename = zipfile_generator(multimedia_res, batch_res,
                                           params={"genus": genus, "family": family, "dataset": dataset})
        response.headers['X-filename'] = filename
        return FileResponse(path=path, filename=filename)
    return multimedia_res


@router.get("/multimedia/{ark_id}", tags=["Multimedia"], response_model=schemas.MultimediaChild)
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


@router.get("/iq/", tags=["Image Quality Metadata"], response_model=List[schemas.IQ])
async def read_iqs(api_key: str = Security(get_api_key), skip: int = 0, limit: int = 100,
                   db: Session = Depends(get_db)):
    '''
        PRIVATE METHOD
        get image quality metadatas
        - param skip: start index
        - param limit: specify the number of records to return
        - return: image quality metadata lists
    '''
    iqs = crud.get_iqs(db, skip=skip, limit=limit)
    return iqs


@router.post("/batch/", tags=['Batch'], response_model=schemas.BatchMetadatum)
async def create_batch(api_key: str = Security(get_api_key),
                       institutionCode: str = Form(None),
                       batchName: str = Form(None),
                       pipeline: schemas.Pipeline = Form(None),
                       creator: str = Form(None),
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
    batch = await crud.create_batch(db, institution=institutionCode, pipeline=pipeline,
                              creator=creator, comment=creatorComments, codeRepo=codeRepository, url=URL,
                              dataset=datasetName, citation=bibliographicCitation, supplement_file= supplementFile,api_key= api_key)
    if batch is None or isinstance(batch,str):
        raise HTTPException(status_code=404, detail="New batch creation failed. Please try again")
    return batch


@router.get("/batch/{batch_ark_id}", tags=['Batch'], response_model=schemas.BatchMetadatum)
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
    return batch


@router.get("/batch/", tags=['Batch'], response_model=schemas.BatchMetadatum)
async def get_batchlist(batch_ark_id: str, api_key: str = Security(get_api_key),
                        db: Session = Depends(get_db)):
    '''
        PRIVATE METHOD
        return all batches by user(later)
        - param institution: Institution Code
        - param batchName: Batch name
        - param pipeline: Source File/Bounding-Box/Segmentation/Landmark
        - param creator: creator name
        - param comment: creator comment
        - param codeRepository: code repository
        - param url: dataset/citation/website url
        - param dataset: fish(default)/bird/etc..
        - param citation: citation info
        - return: New Batch
    '''
    batch = ""
    if batch is None or batch is str:
        raise HTTPException(status_code=404, detail="New batch creation failed. Please try again")
    return batch


# upload image & metadata together
@router.post("/uploadImage/", tags=["Upload"])
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
        - param: batch_ARKID:
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
    if isinstance(new_multimedia,str):
        raise HTTPException(status_code=400, detail=new_multimedia)
    return {
        'status': 'success',
        'ark_id': new_multimedia.ark_id
    }


# reupload image again if image has some issue.
@router.post("/reUploadImage/", tags=["Upload"])
async def re_upload_image(ark_id: str,
                          file: UploadFile = File(..., description="file"),
                          db: Session = Depends(get_db)):
    '''
        PRIVATE METHOD
        upload files streaming
        - param: Image File (size < 20mb, image type：JPEG/JPG/PNG/BMP/GIF)
        - param: ark_id:
        - return: upload success/failure and associate message:?
    '''
    image_validate_error = uploadFileValidation(file)
    if image_validate_error != '':
        raise HTTPException(status_code=400, detail=image_validate_error)
    return 'reupload success'


def calculate_md5(file):
    file_hash = hashlib.md4()
    while chunk := file.read(8192):
        file_hash.update(chunk)
    return file_hash.hexdigest()


base_dir = os.path.dirname(os.path.abspath(__file__))
upload_file_path = Path(base_dir, './uploads')

#
# @router.post("/file-slice")
# async def upload_file(
#         request: Request,
#         identifier: str = Body(..., description="md5"),
#         number: str = Body(..., description="slice no."),
#         file: UploadFile = File(..., description="file")
# ):
#     """upload file slices"""
#     path = Path(upload_file_path, identifier)
#     if not os.path.exists(path):
#         os.makedirs(path)
#     file_name = Path(path, f'{identifier}_{number}')
#     if not os.path.exists(file_name):
#         async with aiofiles.open(file_name, 'wb') as f:
#             await f.write(await file.read())
#     return {
#         'code': 1,
#         'chunk': f'{identifier}_{number}'
#     }
#
#
# @router.put("/file-slice")
# async def merge_file(
#         request: Request,
#         name: str = Body(..., description="filename"),
#         file_type: str = Body(..., description="file-extension"),
#         identifier: str = Body(..., description="md5")
# ):
#     """merge slices files"""
#     target_file_name = Path(upload_file_path, f'{name}.{file_type}')
#     path = Path(upload_file_path, identifier)
#     try:
#         async with aiofiles.open(target_file_name, 'wb+') as target_file:  # 打开目标文件
#             for i in range(len(os.listdir(path))):
#                 temp_file_name = Path(path, f'{identifier}_{i}')
#                 async with aiofiles.open(temp_file_name, 'rb') as temp_file:  # 按序打开每个分片
#                     data = await temp_file.read()
#                     await target_file.write(data)  # 分片内容写入目标文件
#     except Exception as e:
#         return {
#             'code': 0,
#             'error': f'merge failed：{e}'
#         }
#     shutil.rmtree(path)  # 删除临时目录
#     return {
#         'code': 1,
#         'name': f'{name}.{file_type}'
#     }
#
#
# @router.get("/file-slice/{file_name}")
# async def download_file(request: Request, file_name: str = F_Path(..., description="file name（extension included）")):
#     """download file slices，resumable"""
#     # 检查文件是否存在
#     file_path = Path(upload_file_path, file_name)
#     if not os.path.exists(file_path):
#         return {
#             'code': 0,
#             'error': 'file does not exist'
#         }
#     # 获取文件的信息
#     stat_result = os.stat(file_path)
#     content_type, encoding = guess_type(file_path)
#     content_type = content_type or 'application/octet-stream'
#     # 读取文件的起始位置和终止位置
#     range_str = request.headers.get('range', '')
#     range_match = re.search(r'bytes=(\d+)-(\d+)', range_str, re.S) or re.search(r'bytes=(\d+)-', range_str, re.S)
#     if range_match:
#         start_bytes = int(range_match.group(1))
#         end_bytes = int(range_match.group(2)) if range_match.lastindex == 2 else stat_result.st_size - 1
#     else:
#         start_bytes = 0
#         end_bytes = stat_result.st_size - 1
#     # 这里 content_length 表示剩余待传输的文件字节长度
#     content_length = stat_result.st_size - start_bytes if stat.S_ISREG(stat_result.st_mode) else stat_result.st_size
#     # 构建文件名称
#     name, *suffix = file_name.rsplit('.', 1)
#     suffix = f'.{suffix[0]}' if suffix else ''
#     filename = quote(f'{name}{suffix}')
#
#     return StreamingResponse(
#         file_iterator(file_path, start_bytes, 1024 * 1024 * 1),  # read 1mb everytime
#         media_type=content_type,
#         headers={
#             'content-disposition': f'attachment; filename="{filename}"',
#             'accept-ranges': 'bytes',
#             'connection': 'keep-alive',
#             'content-length': str(content_length),
#             'content-range': f'bytes {start_bytes}-{end_bytes}/{stat_result.st_size}',
#             'last-modified': formatdate(stat_result.st_mtime, usegmt=True),
#             'ETag': str(request.headers)
#         },
#         status_code=206 if start_bytes > 0 else 200
#     )
#
#
# def file_iterator(file_path, offset, chunk_size):
#     """
#     文件生成器
#     :param file_path: 文件绝对路径
#     :param offset: 文件读取的起始位置
#     :param chunk_size: 文件读取的块大小
#     :return: yield
#     """
#     with open(file_path, 'rb') as f:
#         f.seek(offset, os.SEEK_SET)
#         while True:
#             data = f.read(chunk_size)
#             if data:
#                 yield data
#             else:
#                 break


app.include_router(router)
