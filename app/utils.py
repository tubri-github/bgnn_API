import os
import app.config as config
import zipstream as zipstream
import uuid
import random
from . import model_text
from noid.pynoid import *
from jinja2 import Template, FileSystemLoader, Environment
from datetime import datetime


## random + uuid generator
def random_str(num=6):
    uln = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    rs = random.sample(uln, num)
    a = uuid.uuid1()
    b = ''.join(rs + str(a).split("-"))
    return b


def zipfile_generator(results, batch_results, params):
    dataset_ark_id_results = minter(config.ARK_DATASETS)
    dataset_ark_id = dataset_ark_id_results[2]
    current_date = datetime.now().strftime("%Y-%m-%d")
    zf = zipstream.ZipFile(compression=zipstream.ZIP_DEFLATED)
    file_list = ["meta.xml", "rdf.owl"]
    for file in file_list:
        basicFilesSourcePath = os.path.join(config.ZIPFILES_PATH, file).replace("\\", "/");
        basicFilesTargetPath = os.path.join('Fish-AIR/Tulane/' + dataset_ark_id + '/', file).replace("\\", "/")
        zf.write(basicFilesSourcePath, basicFilesTargetPath, zipstream.ZIP_DEFLATED)

    #multimedia.csv
    multimedia_csv, multimedia_count = csv_generator(results, type="multimedia")

    #extended md.csv
    extended_metadata_image_csv, extend_data_count = csv_generator(results, type="extended")

    #IQ.csv
    quality_metadata_image_csv, quality_data_count = csv_generator(results, type="quality")
    batch_csv, citation_info = batch_citation_generator(batch_results)
    metadata_xml = metadata_generator(dataset_ark_id,params, current_date )
    zf.write_iter(os.path.join('Fish-AIR/Tulane/' + dataset_ark_id + '/', "multimedia.csv"), iterable(multimedia_csv))
    zf.write_iter(os.path.join('Fish-AIR/Tulane/' + dataset_ark_id + '/', "extendedImageMetadata.csv"), iterable(extended_metadata_image_csv))
    if quality_data_count > 0:
        zf.write_iter(os.path.join('Fish-AIR/Tulane/' + dataset_ark_id + '/', "imageQualityMetadata.csv"), iterable(quality_metadata_image_csv))

    #batch
    zf.write_iter(os.path.join('Fish-AIR/Tulane/' + dataset_ark_id + '/', "batch.csv"), iterable(batch_csv))

    #citations
    zf.write_iter(os.path.join('Fish-AIR/Tulane/' + dataset_ark_id + '/', "citations.txt"), iterable(citation_info))

    #metadata.xml
    zf.write_iter(os.path.join('Fish-AIR/Tulane/' + dataset_ark_id + '/', "metadata.xml"), iterable(metadata_xml))

    zf.filename = "Fish-AIR_" + dataset_ark_id + ".zip"
    with open(os.path.join(zf.filename), 'wb') as f:
        for data in zf:
            f.write(data)
    return os.path.join(zf.filename), zf.filename


def csv_generator(results, type):
    data_count = 0
    if type == 'multimedia':
        csv_header = "arkID,parentArkId,accessURI,createDate,modifyDate,fileNameAsDelivered,format,scientificName,genus,family,batchName,license,source,ownerInstitutionCode\n"
        csv_body = ""
        for record in results:
            recstring = str(record.ark_id) + ',' + str(record.parent_ark_id) + ',' + str(
                record.path) + ',' + str(record.create_date) + ',' + str(record.modify_date) + ',\"' + str(
                record.filename_as_delivered) + '\",' + str(record.format) + ',\"' +\
                       str(record.scientific_name)+'\",' + str(record.genus) + ',' + str(record.family) + ',' + str(record.batch_id) + ',' + str(record.license) + ',' + str(
                record.source) + ',' + str(record.owner_institution_code) + '\n'
            csv_body += recstring
            data_count = data_count + 1
        return csv_header + csv_body, data_count
    if type == 'extended':
        csv_header = "arkId,fileNameAsDelivered,format,createDate,metadataDate,size,width,height,license,publisher,ownerInstitutionCode\n"
        csv_body = ""
        for record in results:
            recstring = str(record.extended_metadata[0].ark_id) + ',\"' + str(record.filename_as_delivered) + '\",' + str(
                record.format) + ',' + str(record.extended_metadata[0].create_date) + ',' + str(
                record.extended_metadata[0].metadata_date) + ',' + str(record.extended_metadata[0].size) + ',' + \
                        str(record.extended_metadata[0].width) + ',' + str(
                record.extended_metadata[0].height) + ',' + str(record.extended_metadata[0].license) + ',' + str(
                record.extended_metadata[0].publisher) + ',' + str(
                record.extended_metadata[0].owner_institution_code) + '\n'
            csv_body += recstring
            data_count = data_count + 1
        return csv_header + csv_body, data_count
    if type == 'quality':
        csv_header = "arkID,license,publisher,ownerInstitutionCode,createDate,metadataDate,specimenQuantity," \
                     "containsScaleBar,containsLabel,accessionNumberValidity,containsBarcode,containsColorBar," \
                     "nonSpecimenObjects,partsOverlapping,specimenAngle,specimenView,specimenCurved,partsMissing," \
                     "allPartsVisible,partsFolded,brightness,uniformBackground,onFocus,colorIssue,quality," \
                     "resourceCreationTechnique\n "
        csv_body = ""
        for record in results:
            if len(record.quality_metadata) > 0:
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
                            + ',\"' + str(record.quality_metadata[0].non_specimen_objects) + '\"' \
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
                            + ',\"' + str(record.quality_metadata[0].color_issue) + "\"" \
                            + ',' + str(record.quality_metadata[0].quality) \
                            + ',' + str(record.quality_metadata[0].data_capture_method) \
                            + '\n'
                csv_body += recstring
                data_count = data_count + 1
        return csv_header + csv_body, data_count

def batch_citation_generator(results):
    # citations
    citation_firstline = "Multimedia of Fish Specimen and associated metadata. Biology guided Neural Network. Tulane University Biodiversity Research Institute (https://bgnn.tulane.edu).\n"
    citation_body = ""

    # batch
    csv_header = "arkId,batchName,institutionCode,pipeline,createDate,modifyDate,creator,creatorComments,contactor,labCode,projectName,codeRepository,datasetName,bibliographicCitation,URL\n "
    csv_body = ""
    for record in results:
        recstring = str(record.ark_id) \
                    + ',' + str(record.batch_name) \
                    + ',' + str(record.institution_code) \
                    + ',' + str(record.pipeline) \
                    + ',' + str(record.create_date) \
                    + ',' + str(record.modify_date) \
                    + ',' + str(record.creator) \
                    + ',' + str(record.creator_comment) \
                    + ',' + str(record.contactor) \
                    + ',' + str(record.lab_code) \
                    + ',' + str(record.project_name) \
                    + ',' + str(record.code_repository) \
                    + ',' + str(record.dataset_name) \
                    + ',' + str(record.bibliographic_citation) \
                    + ',' + str(record.url) \
                    + '\n'
        csv_body += recstring

        citation_body += record.bibliographic_citation + '\n'
    batch_content = csv_header + csv_body
    citation_content = citation_firstline + citation_body
    return batch_content, citation_content

def metadata_generator(dataset_ark_id, params, current_date):
    j2_loader = FileSystemLoader(config.ZIPFILES_PATH)
    env = Environment(loader=j2_loader)
    metadata_template = env.get_template('./metadata.xml')
    metadata_content = metadata_template.render(dataset_ark_id = dataset_ark_id, query_params = params, accessDate=current_date)
    return metadata_content

def iterable(csv):
    yield str.encode(csv)


def minter(ark_type):
    template = 'bat.eeddeedek'
    if ark_type == config.ARK_BATCH:
        template = 'bat.eeddeedek'
    elif ark_type == config.ARK_DATASETS:
        template = 'dts.eeddeedek'
    elif ark_type == config.ARK_MULTIMEDIA:
        template = 'eeddeede'
    ark_id = mint(template=template, scheme='ark:/', naa='89609')
    ark_obj = ark_id.split("/")

    return ark_obj
