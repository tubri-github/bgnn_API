import os
import app.config as config
import zipstream as zipstream
import uuid
import random
from . import model_text
from noid.pynoid import *


## random + uuid generator
def random_str(num=6):
    uln = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    rs = random.sample(uln, num)
    a = uuid.uuid1()
    b = ''.join(rs + str(a).split("-"))
    return b


def zipfile_generator(results):
    zf = zipstream.ZipFile(compression=zipstream.ZIP_DEFLATED)
    file_list = ["meta.xml", "metadata.xml", "citations.txt", "bgnn_rdf_prototype.owl"]
    for file in file_list:
        basicFilesSourcePath = os.path.join(config.ZIPFILES_PATH, file).replace("\\", "/");
        basicFilesTargetPath = os.path.join('bgnn', file).replace("\\", "/")
        zf.write(basicFilesSourcePath, basicFilesTargetPath, zipstream.ZIP_DEFLATED)
    multimedia_csv = csv_generator(results, type="multimedia")
    extended_metadata_image_csv = csv_generator(results, type="extended")
    quality_metadata_image_csv = csv_generator(results, type="quality")
    zf.write_iter(os.path.join("bgnn", "multimedia.csv"), iterable(multimedia_csv))
    zf.write_iter(os.path.join("bgnn", "extendedImageMetadata.csv"), iterable(extended_metadata_image_csv))
    zf.write_iter(os.path.join("bgnn", "imageQualityMetadata.csv"), iterable(quality_metadata_image_csv))
    zf.filename = "bgnn_api" + random_str() + ".zip"
    with open(os.path.join(zf.filename), 'wb') as f:
        for data in zf:
            f.write(data)
    return os.path.join(zf.filename), zf.filename


def csv_generator(results, type):
    if type == 'multimedia':
        csv_header = "arkID,parentArkId,accessURI,createDate,modifyDate,fileNameAsDelivered,format,batchName,license,source,ownerInstitutionCode\n"
        csv_body = ""
        for record in results:
            recstring = str(record.ark_id) + ',' + str(record.parent_ark_id) + ',' + str(
                record.path) + ',' + str(record.create_date) + ',' + str(record.modify_date) + ',' + str(
                record.filename_as_delivered) + ',' + \
                        str(record.format) + ',' + str(record.batch_id) + ',' + str(record.license) + ',' + str(
                record.source) + ',' + str(record.owner_institution_code) + '\n'
            csv_body += recstring
        return csv_header + recstring
    if type == 'extended':
        csv_header = "arkId,fileNameAsDelivered,format,createDate,metadataDate,size,width,height,license,publisher,ownerInstitutionCode\n"
        csv_body = ""
        for record in results:
            recstring = str(record.extended_metadata[0].ark_id) + ',' + str(record.filename_as_delivered) + ',' + str(
                record.format) + ',' + str(record.extended_metadata[0].create_date) + ',' + str(
                record.extended_metadata[0].metadata_date) + ',' + str(record.extended_metadata[0].size) + ',' + \
                        str(record.extended_metadata[0].width) + ',' + str(
                record.extended_metadata[0].height) + ',' + str(record.extended_metadata[0].license) + ',' + str(
                record.extended_metadata[0].publisher) + ',' + str(
                record.extended_metadata[0].owner_institution_code) + '\n'
            csv_body += recstring
        return csv_header + csv_body
    if type == 'quality':
        csv_header = "arkID,license,publisher,ownerInstitutionCode,createDate,metadataDate,specimenQuantity," \
                     "containsScaleBar,containsLabel,accessionNumberValidity,containsBarcode,containsColorBar," \
                     "nonSpecimenObjects,partsOverlapping,specimenAngle,specimenView,specimenCurved,partsMissing," \
                     "allPartsVisible,partsFolded,brightness,uniformBackground,onFocus,colorIssue,quality," \
                     "resourceCreationTechnique\n "
        csv_body = ""
        for record in results:
            recstring = str(record.quality_metadata[0].ark_id) \
                        + ',' + str(record.quality_metadata[0].license) \
                        + ',' + str(record.quality_metadata[0].publisher) \
                        + ',' + str(record.quality_metadata[0].owner_institution_code) \
                        + ',' + str(record.quality_metadata[0].create_date) \
                        + ',' + str(record.quality_metadata[0].metadata_date) \
                        + ',' + str(record.quality_metadata[0].specimen_quantity) \
                        + ',' + str(record.quality_metadata[0].contains_scalebar) \
                        + ',' + str(record.quality_metadata[0].contains_label) \
                        + ',' + str(record.quality_metadata[0].accession_number_validity) \
                        + ',' + str(record.quality_metadata[0].contains_barcode) \
                        + ',' + str(record.quality_metadata[0].contains_colorbar) \
                        + ',' + str(record.quality_metadata[0].non_specimen_objects) \
                        + ',' + str(record.quality_metadata[0].parts_overlapping) \
                        + ',' + str(record.quality_metadata[0].specimen_angle) \
                        + ',' + str(record.quality_metadata[0].specimen_view) \
                        + ',' + str(record.quality_metadata[0].specimen_curved) \
                        + ',' + str(record.quality_metadata[0].parts_missing) \
                        + ',' + str(record.quality_metadata[0].all_parts_visible) \
                        + ',' + str(record.quality_metadata[0].parts_folded) \
                        + ',' + str(record.quality_metadata[0].brightness) \
                        + ',' + str(record.quality_metadata[0].uniform_background) \
                        + ',' + str(record.quality_metadata[0].on_focus) \
                        + ',' + str(record.quality_metadata[0].color_issue) \
                        + ',' + str(record.quality_metadata[0].quality) \
                        + ',' + str(record.quality_metadata[0].data_capture_method) \
                        + '\n'
            csv_body += recstring
        return csv_header + csv_body


def iterable(csv):
    yield str.encode(csv)


def minter(ark_type):
    template = 'bat.eeddeedek'
    if ark_type == "batch":
        template = 'bat.eeddeedek'
    elif ark_type == "datasets":
        template = 'dtseeddeedek'
    elif ark_type == "multimedia":
        template = 'eeddeede'
    ark_id = mint(template=template, scheme='ark:/', naa='89609')

    return ark_id
