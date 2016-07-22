import email
import zipfile
import os
import gzip
import string
import boto3


print('Loading function')

s3 = boto3.client('s3')


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'])

    try:
        # Use waiter to ensure the file is persisted
        waiter = s3.get_waiter('object_exists')
        waiter.wait(Bucket=bucket, Key=key)
        response = s3.Object(Bucket=bucket, Key=key)

        msg = email.message_from_string(object.get()["Body"].read())

        if len(msg.get_payload()) == 2:
            
            attachment = msg.get_payload()[1]
            xmlDir = "/tmp/output/"
            
            # Create directory for XML files (makes debugging easier)
            if os.path.isdir(xmlDir) == False:
                os.mkdir(xmlDir)
            
            # Process filename.zip attachments 
            if attachment.get_content_type() == "application/x-zip-compressed":
                print('ZIP')
                open('/tmp/attachment.zip', 'wb').write(attachment.get_payload(decode=True))
                with zipfile.ZipFile('/tmp/attachment.zip', "r") as z:
                    z.extractall(xmlDir)
            
            # Process filename.xml.gz attachments (Providers not complying to standards)
            elif attachment.get_content_type() == "application/gzip":
                contentdisp = string.split(attachment.get('Content-Disposition'), '=')
                fname = contentdisp[1].replace('\"','')
                
                open('/tmp/'+contentdisp[1], 'wb').write(attachment.get_payload(decode=True))
                
                # This assumes we have filename.xml.gz, if we get this wrong, we will just 
                # ignore the report
                xmlname = fname[:-3]
                open(xmlDir+xmlname, 'wb').write(gzip.open('/tmp/'+contentdisp[1], 'rb').read())
                
            else:
                print('Skipping' + attachment.get_content_type())
                
                
            # Put all XML back into S3 (Covers non-compliant cases if a ZIP contains multiple results)
            import os
            for file in os.listdir(xmlDir):
                if file.endswith(".xml"):
                    print(file) # File name to upload
                
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist '
          'and your bucket is in the same region as this '
          'function.'.format(key, bucket))
        raise e
