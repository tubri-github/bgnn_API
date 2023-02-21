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
    Path as F_Path
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.responses import StreamingResponse

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
async def read_multimedias(response: Response, api_key: str = Security(get_api_key), genus: Optional[str] = None,
                           family: Optional[str] = None, dataset: schemas.DatasetName = None, zipfile: bool = True,
                           db: Session = Depends(get_db)
                           ):
    '''
        PRIVATE METHOD
        get multimedias and associated (meta)data, like IQ, extended metadata, hirecachy medias
        - param genus: species genus
        - param family: species family
        - param dataset: dataset name
        - param zipfile: return JSON or Zip file
        - return: multimedia lists(with associated (meta)data). If zipfile is false, it will return 20 records (pagination required)
    '''
    # multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, dataset=dataset,min_height=min_height,max_height=max_height, limit=limit)
    multimedia_res, batch_res = crud.get_multimedias(db, genus=genus, family=family, dataset=dataset, zipfile=zipfile)
    if zipfile:
        # path, filename = zipfile_generator(multimedia_res, batch_res, params={"genus": genus, "dataset": dataset, "min_height": min_height, "max_height": max_height,"limit": limit})
        path, filename = zipfile_generator(multimedia_res, batch_res,
                                           params={"genus": genus, "family": family, "dataset": dataset})
        response.headers['X-filename'] = filename
        return FileResponse(path=path, filename=filename)
    return multimedia_res


@router.get("/multimedia_public/", tags=["Multimedia"], response_model=List[schemas.MultimediaChild])
# async def read_multimedias(response: Response, genus: Optional[str] = None, dataset: schemas.DatasetName = schemas.DatasetName.glindataset, min_height: Optional[int] = None, max_height: Optional[int] = None, limit: Optional[int] = None, zipfile: bool = True,
async def read_multimedias(response: Response, genus: Optional[str] = None, family: Optional[str] = None,
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


# upload public

@router.post("/upload/", tags=["Upload"])
async def upload_files(api_key: str = Security(get_api_key)):
    '''
        PRIVATE METHOD
        upload files streaming
        - param skip: start index
        - param limit: specify the number of records to return
        - return: upload success/failure and associate message:?
    '''
    # md5 check

    # upload chunks
    return '3'


def calculate_md5(file):
    file_hash = hashlib.md4()
    while chunk := file.read(8192):
        file_hash.update(chunk)
    return file_hash.hexdigest()


base_dir = os.path.dirname(os.path.abspath(__file__))
upload_file_path = Path(base_dir, './uploads')


@router.post("/file-slice")
async def upload_file(
        request: Request,
        identifier: str = Body(..., description="md5"),
        number: str = Body(..., description="slice no."),
        file: UploadFile = File(..., description="file")
):
    """upload file slices"""
    path = Path(upload_file_path, identifier)
    if not os.path.exists(path):
        os.makedirs(path)
    file_name = Path(path, f'{identifier}_{number}')
    if not os.path.exists(file_name):
        async with aiofiles.open(file_name, 'wb') as f:
            await f.write(await file.read())
    return {
        'code': 1,
        'chunk': f'{identifier}_{number}'
    }


@router.put("/file-slice")
async def merge_file(
        request: Request,
        name: str = Body(..., description="filename"),
        file_type: str = Body(..., description="file-extension"),
        identifier: str = Body(..., description="md5")
):
    """merge slices files"""
    target_file_name = Path(upload_file_path, f'{name}.{file_type}')
    path = Path(upload_file_path, identifier)
    try:
        async with aiofiles.open(target_file_name, 'wb+') as target_file:  # 打开目标文件
            for i in range(len(os.listdir(path))):
                temp_file_name = Path(path, f'{identifier}_{i}')
                async with aiofiles.open(temp_file_name, 'rb') as temp_file:  # 按序打开每个分片
                    data = await temp_file.read()
                    await target_file.write(data)  # 分片内容写入目标文件
    except Exception as e:
        return {
            'code': 0,
            'error': f'merge failed：{e}'
        }
    shutil.rmtree(path)  # 删除临时目录
    return {
        'code': 1,
        'name': f'{name}.{file_type}'
    }


@router.get("/file-slice/{file_name}")
async def download_file(request: Request, file_name: str = F_Path(..., description="file name（extension included）")):
    """download file slices，resumable"""
    # 检查文件是否存在
    file_path = Path(upload_file_path, file_name)
    if not os.path.exists(file_path):
        return {
            'code': 0,
            'error': 'file does not exist'
        }
    # 获取文件的信息
    stat_result = os.stat(file_path)
    content_type, encoding = guess_type(file_path)
    content_type = content_type or 'application/octet-stream'
    # 读取文件的起始位置和终止位置
    range_str = request.headers.get('range', '')
    range_match = re.search(r'bytes=(\d+)-(\d+)', range_str, re.S) or re.search(r'bytes=(\d+)-', range_str, re.S)
    if range_match:
        start_bytes = int(range_match.group(1))
        end_bytes = int(range_match.group(2)) if range_match.lastindex == 2 else stat_result.st_size - 1
    else:
        start_bytes = 0
        end_bytes = stat_result.st_size - 1
    # 这里 content_length 表示剩余待传输的文件字节长度
    content_length = stat_result.st_size - start_bytes if stat.S_ISREG(stat_result.st_mode) else stat_result.st_size
    # 构建文件名称
    name, *suffix = file_name.rsplit('.', 1)
    suffix = f'.{suffix[0]}' if suffix else ''
    filename = quote(f'{name}{suffix}')

    return StreamingResponse(
        file_iterator(file_path, start_bytes, 1024 * 1024 * 1),  # read 1mb everytime
        media_type=content_type,
        headers={
            'content-disposition': f'attachment; filename="{filename}"',
            'accept-ranges': 'bytes',
            'connection': 'keep-alive',
            'content-length': str(content_length),
            'content-range': f'bytes {start_bytes}-{end_bytes}/{stat_result.st_size}',
            'last-modified': formatdate(stat_result.st_mtime, usegmt=True),
            'ETag': str(request.headers)
        },
        status_code=206 if start_bytes > 0 else 200
    )


def file_iterator(file_path, offset, chunk_size):
    """
    文件生成器
    :param file_path: 文件绝对路径
    :param offset: 文件读取的起始位置
    :param chunk_size: 文件读取的块大小
    :return: yield
    """
    with open(file_path, 'rb') as f:
        f.seek(offset, os.SEEK_SET)
        while True:
            data = f.read(chunk_size)
            if data:
                yield data
            else:
                break


app.include_router(router)
