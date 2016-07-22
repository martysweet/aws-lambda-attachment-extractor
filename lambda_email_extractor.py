from __future__ import print_function

import email
import zipfile
import os
import gzip
import string
import boto3
import urllib

print('Loading function')

s3 = boto3.client('s3')
xmlDir = "/tmp/output/"

outputBucket = "security-dmarc-raw"
outputPrefix = "xml/" # Should end with /


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).decode('uft8')

    try:
        # Use waiter to ensure the file is persisted
        waiter = s3.get_waiter('object_exists')
        waiter.wait(Bucket=bucket, Key=key)
        response = s3.Object(Bucket=bucket, Key=key)

        # Read the raw text file into a Email Object
        msg = email.message_from_string(response.get()["Body"].read())

        if len(msg.get_payload()) == 2:

            # Create directory for XML files (makes debugging easier)
            if os.path.isdir(xmlDir) == False:
                os.mkdir(xmlDir)

            # The first attachment
            attachment = msg.get_payload()[1]

            # Extract the attachment into /tmp/output
            extract_attachment(attachment)

            # Upload the XML files to S3
            upload_resulting_files_to_s3()

        else:
            print("Could not see file/attachment.")

    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist '
            'and your bucket is in the same region as this '
            'function.'.format(key, bucket))
        raise e


def extract_attachment(attachment):
    # Process filename.zip attachments
    if attachment.get_content_type() == "application/x-zip-compressed":
        open('/tmp/attachment.zip', 'wb').write(attachment.get_payload(decode=True))
        with zipfile.ZipFile('/tmp/attachment.zip', "r") as z:
            z.extractall(xmlDir)

    # Process filename.xml.gz attachments (Providers not complying to standards)
    elif attachment.get_content_type() == "application/gzip":
        contentdisp = string.split(attachment.get('Content-Disposition'), '=')
        fname = contentdisp[1].replace('\"', '')
        open('/tmp/' + contentdisp[1], 'wb').write(attachment.get_payload(decode=True))
        # This assumes we have filename.xml.gz, if we get this wrong, we will just
        # ignore the report
        xmlname = fname[:-3]
        open(xmlDir + xmlname, 'wb').write(gzip.open('/tmp/' + contentdisp[1], 'rb').read())

    else:
        print('Skipping' + attachment.get_content_type())


def upload_resulting_files_to_s3():
    # Put all XML back into S3 (Covers non-compliant cases if a ZIP contains multiple results)
    k = s3.Key(outputBucket)
    for fileName in os.listdir(xmlDir):
        if fileName.endswith(".xml"):
            print("Uploading: " + fileName)  # File name to upload
            k.key = outputPrefix + fileName
            k.set_contents_from_file(open(xmlDir+'/'+fileName))
