import os
import app.config as config
import zipstream as zipstream
import uuid
import random
from . import model_text

## random + uuid generator
def random_str(num=6):
    uln = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    rs = random.sample(uln, num)
    a = uuid.uuid1()
    b = ''.join(rs + str(a).split("-"))
    return b

def zipfile_generator(results):
    zf = zipstream.ZipFile(compression=zipstream.ZIP_DEFLATED)
    file_list = ["meta.xml","metadata.xml","citations.txt","bgnn_rdf_prototype.owl"]
    for file in file_list:
        basicFilesSourcePath = os.path.join(config.ZIPFILES_PATH, file).replace("\\", "/");
        basicFilesTargetPath = os.path.join('bgnn', file).replace("\\", "/")
        zf.write(basicFilesSourcePath, basicFilesTargetPath, zipstream.ZIP_DEFLATED)
    multimedia_csv = csv_generator(results, type="multimedia")
    extended_metadata_image_csv = csv_generator(results, type="extended")
    zf.write_iter(os.path.join("bgnn","multimedia.csv"), iterable(multimedia_csv))
    zf.write_iter(os.path.join("bgnn","extendedImageMetadata.csv"), iterable(extended_metadata_image_csv))
    zf.filename = "bgnn_api" + random_str() + ".zip"
    with open(os.path.join(zf.filename), 'wb') as f:
        for data in zf:
            f.write(data)
    return os.path.join(zf.filename), zf.filename

def csv_generator(results,type):
    if type == 'multimedia':
        csv_header = "arkID,parentArkId,accessURI,createDate,modifyDate,fileNameAsDelivered,format,batchName,license,source,ownerInstitutionCode\n"
        csv_body = ""
        for record in results:
            recstring = str(record.ark_id) + ',' + str(record.parent_ark_id) + ',' + str(
            record.path ) + ',' + str(record.create_date) + ',' + str(record.modify_date) +  ',' + str(record.filename_as_delivered) + ',' +\
                    str(record.format) +  ',' + str(record.batch_id) +  ',' + str(record.license) +  ',' + str(record.source) +  ',' + str(record.owner_institution_code) + '\n'
            csv_body += recstring
        return csv_header + recstring
    if type == 'extended':
        csv_header = "arkId,fileNameAsDelivered,format,createDate,metadataDate,size,width,height,license,publisher,ownerInstitutionCode\n"
        csv_body = ""
        for record in results:
            recstring = str(record.extended_metadata[0].ark_id) + ',' + str(record.filename_as_delivered) + ',' + str(
            record.format ) + ',' + str(record.extended_metadata[0].create_date) + ',' + str(record.extended_metadata[0].metadata_date) +  ',' + str(record.extended_metadata[0].size) + ',' +\
                    str(record.extended_metadata[0].width) +  ',' + str(record.extended_metadata[0].height) +  ',' + str(record.extended_metadata[0].license) +  ',' + str(record.extended_metadata[0].publisher) +  ',' + str(record.extended_metadata[0].owner_institution_code) + '\n'
            csv_body += recstring
        return csv_header + csv_body

def iterable(csv):
    yield str.encode(csv)