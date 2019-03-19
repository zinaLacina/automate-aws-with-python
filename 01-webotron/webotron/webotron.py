import boto3
import click
from botocore.exceptions import ClientError
from pathlib import Path
import mimetypes
session = boto3.session.Session(profile_name='zina')
s3 = session.resource('s3')




@click.group()
def cli():
    "Webotron deploys websites to AWS"
    pass


@cli.command('list-buckets')
def list_buckets():
    "List all s3 buckets"
    for bucket in s3.buckets.all():
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    "List the objects of an s3 bucket"
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    "Create and Configure a bucket"
    s3_bucket = None
    try:
        s3_bucket = s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={
                'LocationConstraint': session.region_name}
        )
    except ClientError as e:
        if e.response['error']['code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
        else:
            raise e
    # Policy configuration
    policy = """
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadgetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::%s/*"
                }
            ]
        }
        """ % s3_bucket.name
    pol = s3_bucket.Policy()
    policy = policy.strip()
    pol.put(Policy=policy)

    # Website configuration
    ws = s3_bucket.Website()
    ws.put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.httml'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }
    })
    url = "http://%s.s3-website-ap-northeast-1.amazonaws.com" % s3_bucket.name

    return url

def upload_file(s3_bucket, path, key):
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    s3_bucket.upload_file(
        path,
        key,
        ExtraArgs={
            'ContentType': 'text/html'
        })

@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    "Sync contents of PATHNAME to BUCKET"
    s3_bucket = s3.Bucket(bucket)

    root = Path(pathname).expanduser().resolve()

    def handle_directory(target):
        for p in target.iterdir():
            if p.is_dir():
                handle_directory(p)
            if p.is_file():
                upload_file(s3_bucket, str(p), str(p.relative_to(root)))

    handle_directory(root)


if __name__ == '__main__':
    cli()
