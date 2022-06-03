import boto3
import json
client = boto3.client('ec2')

vpc_endpoint_response = client.describe_vpc_endpoints(
    Filters=[
        {
            'Name': 'tag:Broker',
            'Values': [
                'b-5c20383f-09af-4141-a6e5-5dea346929c7',
            ]
        },
    ]
)
print(vpc_endpoint_response)

BROKER_ID = 'b-5c20383f-09af-4141-a6e5-5dea346929c7'
NLB_ARN = 'arn:aws:elasticloadbalancing:us-west-2:681921237057:loadbalancer/net/zalando-cdk-demo-nlb/32d3473d173b708d'

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
    target_group_name = BROKER_ID[-32:]

    response = client.describe_listeners(LoadBalancerArn=NLB_ARN)
    
    print(response)

    listener_arn = response['Listeners'][0]['ListenerArn']

    print('Listener ARN {}'.format(listener_arn))

    response = client.describe_load_balancers(LoadBalancerArns=[NLB_ARN])

    vpc_id = response['LoadBalancers'][0]['VpcId']

    response = client.describe_target_health(
        TargetGroupArn='string',
        Targets=[
            {
                'Id': 'string',
                'Port': 123,
                'AvailabilityZone': 'string'
            },
        ]
    )

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

    print('Modify listener response {}'.format(mod_listener_response))
