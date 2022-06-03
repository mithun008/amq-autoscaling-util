import boto3
import json

client = boto3.client('mq')
BROKER_ID = 'xxxx'
INSTANCE_TYPE = 'mq.m5.xlarge'
#response = client.list_brokers(MaxResults=10,NextToken='')
response = client.update_broker(BrokerId=BROKER_ID,HostInstanceType=INSTANCE_TYPE)
print('{} received update broker response: {}'.format('MQTEST', response))