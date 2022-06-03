import boto3
import json
from jsonpath_ng.ext import parse

client = boto3.client('ec2')

f = open("tg-eni-status.json", "r")
eni_status = f.read()

#print(eni_status)

eni_status = json.loads(eni_status)

#print(eni_status)

#target_health_desc = eni_status['HealthStatus']['TargetHealthDescriptions']

#print(json.dumps(eni_status))

json_path_expr = parse("$.HealthStatus.TargetHealthDescriptions[?(@.TargetHealth.State != 'healthy')]")

#eni_registering_status = json_path_expr.find(eni_status)

eni_registering = json_path_expr.find(eni_status)
print(len(eni_registering))
#for match in json_path_expr.find(eni_status):
#	print(match.value)

#print(eni_registering_status)