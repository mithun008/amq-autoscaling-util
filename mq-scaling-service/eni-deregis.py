import boto3
import json
import time
client = boto3.client('ec2')

vpc_endpoint_response = client.describe_vpc_endpoints(
    Filters=[
        {
            'Name': 'tag:Broker',
            'Values': [
                'b-a8bb0c09-41b5-4fcd-a498-8f72af9efe83',
            ]
        },
    ]
)
print(vpc_endpoint_response)

BROKER_ID = 'b-a8bb0c09-41b5-4fcd-a498-8f72af9efe83'
NLB_ARN = 'arn:aws:elasticloadbalancing:us-west-2:681921237057:loadbalancer/net/zalando-cdk-demo-nlb/d946ccda95ebd661'


#print('Target group list {}'.format(tgList))
# update the target group with the new broker ENI
client = boto3.client('elbv2')
target_group_name = BROKER_ID[-32:]

response = client.describe_listeners(LoadBalancerArn=NLB_ARN)
#print('ELB response')
# print(response)

listener_arn = response['Listeners'][0]['ListenerArn']

curr_target_arn = response['Listeners'][0]['DefaultActions'][0]['TargetGroupArn']

print('Target group ARN {}'.format(curr_target_arn))

#print('Listener ARN {}'.format(listener_arn))

response = client.describe_load_balancers(LoadBalancerArns=[NLB_ARN])

vpc_id = response['LoadBalancers'][0]['VpcId']

response = client.describe_target_health(
    TargetGroupArn=curr_target_arn,

)
# print(response)

targets = response['TargetHealthDescriptions']
oldtglist = []
for target in targets:
    print('Target is {}'.format(target))
    target_info = {'Id': target['Target']['Id'], 'Port': 5671,
                   'AvailabilityZone': target['Target']['AvailabilityZone']}
    oldtglist.append(target_info)

print(oldtglist)

response = client.deregister_targets(
    TargetGroupArn=curr_target_arn,
    Targets=oldtglist
)

print(response)
time.sleep(10)
response = client.describe_target_health(
    TargetGroupArn=curr_target_arn,

)
targets = response['TargetHealthDescriptions']
print('Targets {}'.format(targets))
while len(targets) > 0:
    time.sleep(10)
    response = client.describe_target_health(
        TargetGroupArn=curr_target_arn,

    )
    targets = response['TargetHealthDescriptions']
    print('Target healths {}'.format(targets))
    print('Targets length {}'.format(len(targets)))
