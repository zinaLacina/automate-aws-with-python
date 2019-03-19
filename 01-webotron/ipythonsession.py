# coding: utf-8
import boto3
session = boto3.session.Session(profile_name = 'zina')
s3 = session.resource('s3')
for bucket in s3.buckets.all():
    print(bucket)
    
# new_bucket = s3.create_bucket(Bucket='zina-bucket-automatepython',CreateBucketConfiguration={'LocationConstraint':'ap-northeast-1'})
ec2_client = session.client('ec2')
