AWS Lambda Attachment Extractor
===============================

This is a very simple project which can be used for reference when creating Lambda functions to manipulate email 
files stored to an Amazon S3 bucket, typically by an inbound SES routing rule. See 
['AWS Documentation'](http://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email.html) for more information.


Use cases
---------

The original use for this project is to get .ZIP and .GZIP attachments from emails stored in S3, extract the archives,
resulting in .XML files, which are then uploaded to another S3 bucket for processing by another service.

The python file doesn't perform security checks on attachments and will ignore anything which does not 
result in an .XML file. The original email will be deleted after processing takes place.