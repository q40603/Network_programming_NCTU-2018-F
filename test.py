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
python3 /home/ubuntu/5/server.py 0.0.0.0 8080 >> /home/ubuntu/5/console.txt'''
def createInstance():
    print(user_data)
    instance = ec2.create_instances(
        ImageId="ami-0b26213a04f4d5b6e", 
        InstanceType = "t2.micro",  
        SecurityGroupIds=['launch-wizard-1'],
        MinCount=1,
        MaxCount=1,
        KeyName='qq_key',
        UserData=user_data

     )
     # return response
    return instance[0].instance_id

print(createInstance())


