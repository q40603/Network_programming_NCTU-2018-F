from collections import defaultdict

import boto3

"""
A tool for retrieving basic information from the running EC2 instances.
"""

# Connect to EC2
ec2 = boto3.resource('ec2',region_name='us-east-2')

# Get information for all running instances
'''
running_instances = ec2.instances.filter(Filters=[{
    'Name': 'instance-state-name',
    'Values': ['running']}])

ec2info = defaultdict()
for instance in running_instances:
    # Add instance info to a dictionary         
    ec2info[instance.id] = {
        'Type': instance.instance_type,
        'State': instance.state['Name'],
        'Private IP': instance.private_ip_address,
        'Public IP': instance.public_ip_address,
        'Launch Time': instance.launch_time
        }

print(ec2info)
'''
user_data = '''#!/bin/bash
python3 /home/ubuntu/5/model.py
python3 /home/ubuntu/5/server.py 0.0.0.0 8080
'''
def createInstance():
    instance = ec2.create_instances(
        ImageId="ami-0d914ccd1a3279ef5", 
        InstanceType = "t2.micro",  
        SecurityGroupIds=['launch-wizard-1'],
        MinCount=1,
        MaxCount=1,
        KeyName='qq_key',
        UserData=user_data

     )
     # return response
    instance[0].wait_until_running()
    return instance[0].instance_id

server_id = createInstance()
print(server_id)

instance_collection = ec2.instances.filter(InstanceIds=[server_id])
for i in instance_collection:
    print (i.public_ip_address)