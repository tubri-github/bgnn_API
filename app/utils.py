import os
import app.config as config
import zipstream as zipstream
import uuid
import random

## random + uuid generator
def random_str(num=6):
    uln = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    rs = random.sample(uln, num)
    a = uuid.uuid1()
    b = ''.join(rs + str(a).split("-"))
    return b

def zipfile_generator():
    zf = zipstream.ZipFile(compression=zipstream.ZIP_DEFLATED)
    file_list = ["meta.xml","metadata.xml","citations.txt","bgnn_rdf_prototype.owl"]
    for file in file_list:
        basicFilesSourcePath = os.path.join(config.ZIPFILES_PATH, file).replace("\\", "/");
        basicFilesTargetPath = os.path.join('bgnn', file).replace("\\", "/")
        zf.write(basicFilesSourcePath, basicFilesTargetPath, zipstream.ZIP_DEFLATED)
    zf.filename = "bgnn_api" + random_str() + ".zip"
    with open(os.path.join(zf.filename), 'wb') as f:
        for data in zf:
            f.write(data)
    return os.path.join(zf.filename), zf.filename
