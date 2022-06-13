import boto3

import json
import os
import random
import time
from jsonpath_ng.ext import parse

SERVICE_NAME = os.environ['SERVICE_NAME']
BROKER_ID = os.environ['BROKER_ID']
INSTANCE_TYPE = os.environ['INSTANCE_TYPE']

NLB_ARN = os.environ['NLB_ARN']

client = boto3.client('mq')


def lambda_scaling_handler(event, context):
    print('{} received event: {}'.format(SERVICE_NAME, json.dumps(event)))
    print('Broker id  : {}'.format(BROKER_ID))
    print('Instance type : {}'.format(INSTANCE_TYPE))

    # check broker instance type. If its a type which has further room to grow then upgrade or create new.
    # For scale down, check if its bigger than m5.large then scale down.

    # call the MQ API to upscale
    response = client.update_broker(
        BrokerId=BROKER_ID, HostInstanceType=INSTANCE_TYPE)
    print('{} received update broker response: {}'.format(
        SERVICE_NAME, json.dumps(response)))
    # reboot the broker
    response = client.reboot_broker(BrokerId=BROKER_ID)
    print('{} received reboot broker response: {}'.format(
        SERVICE_NAME, json.dumps(response)))

    return


def lambda_brokerstatus_handler(event, context):
    print('{} received event: {}'.format(SERVICE_NAME, json.dumps(event)))

    client = boto3.client('ec2')

    # use new broker id to create a new target group for the ENI's
    new_broker_id = event['detail']['responseElements']['brokerId']
    
    print('New broker {}'.format(new_broker_id))

    vpc_endpoint_response = client.describe_vpc_endpoints(
        Filters=[
            {
                'Name': 'tag:Broker',
                'Values': [
                    new_broker_id,
                ]
            },
        ]
    )

    if not vpc_endpoint_response['VpcEndpoints'][0]['NetworkInterfaceIds'] is None:
        print('The ENI id is {}'.format(
            vpc_endpoint_response['VpcEndpoints'][0]['NetworkInterfaceIds']))
        eni_id_list = vpc_endpoint_response['VpcEndpoints'][0]['NetworkInterfaceIds']

        eni_response = client.describe_network_interfaces(

            NetworkInterfaceIds=eni_id_list
        )
        print('*****')
        print(eni_response)
        network_interfaces = eni_response['NetworkInterfaces']
        print('*****')
        tgList = []
        for eni in network_interfaces:
            print('The private ip addresses are {}'.format(
                eni['PrivateIpAddresses'][0]['PrivateIpAddress']))
            eni_ip = eni['PrivateIpAddresses'][0]['PrivateIpAddress']
            print(eni_ip)
            tg = {"Id": eni_ip, "Port": 5671}
            tgList.append(tg)

        print('Target group list {}'.format(tgList))
    # update the target group with the new broker ENI
    client = boto3.client('elbv2')
    target_group_name = new_broker_id[-32:]

    response = client.describe_listeners(LoadBalancerArn=NLB_ARN)

    listener_arn = response['Listeners'][0]['ListenerArn']
    curr_target_arn = response['Listeners'][0]['DefaultActions'][0]['TargetGroupArn']
    
    response = client.describe_load_balancers(LoadBalancerArns=[NLB_ARN])

    vpc_id = response['LoadBalancers'][0]['VpcId']
    
    
    # deregister current targets
    deregister_current_targets(curr_target_arn)

    # create new target group
    response = client.create_target_group(
        Name=target_group_name,
        Protocol='TCP',
        Port=5671,
        VpcId=vpc_id,
        TargetType='ip',
    )
    target_group_arn = response['TargetGroups'][0]['TargetGroupArn']

    tg_response = client.register_targets(
        TargetGroupArn=target_group_arn, Targets=tgList)

    print('Target group register response {}'.format(tg_response))
    
    mod_listener_response = client.modify_listener(
        DefaultActions=[
            {
                'TargetGroupArn': target_group_arn,
                'Type': 'forward',
            },
        ],
        ListenerArn=listener_arn,
    )

    tg_mod_response = client.modify_target_group_attributes(
        TargetGroupArn=target_group_arn,
        Attributes=[
            {
                'Key': 'deregistration_delay.connection_termination.enabled',
                'Value': 'true'
            },
            {
                'Key': 'deregistration_delay.timeout_seconds',
                'Value': '30'
            },
        ]
    )

    print('Modify target group attributes {}'.format(tg_mod_response))

    print('Modify listener response {}'.format(mod_listener_response))

    targetGroupArn = {"targetGroupArn": target_group_arn}

    return targetGroupArn

def deregister_current_targets(target_group_arn):
    print('Target group ARN {}'.format(target_group_arn))

    #print('Listener ARN {}'.format(listener_arn))
    client = boto3.client('elbv2')

    response = client.describe_load_balancers(LoadBalancerArns=[NLB_ARN])

    #vpc_id = response['LoadBalancers'][0]['VpcId']

    response = client.describe_target_health(
        TargetGroupArn=target_group_arn,

    )
    # print(response)

    targets = response['TargetHealthDescriptions']
    current_tg_list = []
    for target in targets:
        print('Target is {}'.format(target))
        target_info = {'Id': target['Target']['Id'], 'Port': 5671,
                       'AvailabilityZone': target['Target']['AvailabilityZone']}
        current_tg_list.append(target_info)

    print('Current TG List {}'.format(current_tg_list))

    response = client.deregister_targets(
        TargetGroupArn=target_group_arn,
        Targets=current_tg_list
    )
    
    #giving some for connection termination
    time.sleep(50)
    
    response = client.describe_target_health(
        TargetGroupArn=target_group_arn,

    )
    targets = response['TargetHealthDescriptions']
    print('Targets {}'.format(targets))
    print('Targets length {}'.format(len(targets)))
    
    

def lambda_targetenistatus_handler(event, context):
    print(event)
    json_path_expr = parse(
        "$.HealthStatus.TargetHealthDescriptions[?(@.TargetHealth.State != 'healthy')]")
    eni_registering = json_path_expr.find(event)
    num_eni_reg = len(eni_registering)
    print('The registering eni {}'.format(num_eni_reg))
    if num_eni_reg > 0:
        status = {'all_eni_healthy': 'false',
                  'targetGroupArn': event['targetGroupArn']}
    else:
        status = {'all_eni_healthy': 'true',
                  'targetGroupArn': event['targetGroupArn']}

    return status
