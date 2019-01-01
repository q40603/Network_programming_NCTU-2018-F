import sys
import socket
from model import *
import json
import uuid
import time
import stomp
import boto3
connect_to_mq = stomp.Connection([('18.224.6.54', 61613)])
connect_to_mq.start()
connect_to_mq.connect('admin', 'admin', wait=True)
ec2 = boto3.resource('ec2',region_name='us-east-2')
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
    return instance[0].instance_id
class DBControl(object):
    def __auth(func):
        def validate_token(self, token=None, *args):
            if token:
                t = Token.get_or_none(Token.token == token)
                if t:
                    return func(self, t, *args)
            return {
                'status': 1,
                'message': 'Not login yet'
            }
        return validate_token

    def register(self, username=None, password=None, *args):
        if not username or not password or args:
            return {
                'status': 1,
                'message': 'Usage: register <username> <password>'
            }
        if User.get_or_none(User.username == username):
            return {
                'status': 1,
                'message': '{} is already used'.format(username)
            }
        res = User.create(username=username, password=password)
        if res:
            return {
                'status': 0,
                'message': 'Success!'
            }
        else:
            return {
                'status': 1,
                'message': 'Register failed due to unknown reason'
            }

    @__auth
    def delete(self, token, *args):
        if args:
            return {
                'status': 1,
                'message': 'Usage: delete <user>'
            }
        user = token.owner.username
        query = Chat_group.select(Chat_group.group_name).where(Chat_group.member == token.owner)
        res = []
        for group in query:
            res.append(group.group_name)  
        token.owner.delete_instance()
        return {
            'status': 0,
            'message': 'Success!',
            'unsubscribe' : res,
            'user' : user
        }

    def login(self, username=None, password=None, *args):
        if not username or not password or args:
            return {
                'status': 1,
                'message': 'Usage: login <id> <password>'
            }
        res = User.get_or_none((User.username == username) & (User.password == password))
        if res:
            t = Token.get_or_none(Token.owner == res)
            if not t:
                t = Token.create(token=str(uuid.uuid4()), owner=res)
            query = Chat_group.select(Chat_group.group_name).where(Chat_group.member == t.owner)
            res = []
            for group in query:
                res.append(group.group_name)
            check_login = App_server.get_or_none(App_server.user == t.owner)
            if check_login :
                return {
                    'status': 0,
                    'token': t.token,
                    'message': 'Success!',
                    'subscribe': res,
                    'app_server' : check_login.server_ip
                }                
            query_server = App_server.select(App_server.server_ip).group_by(App_server.server_ip).having(fn.Count() < 10)
            if (len(query_server) == 0):
                query_server = createInstance()
            else:
                query_server = query_server[0].server_ip
            record = App_server.create(user = t.owner, server_ip = query_server)
            if record:
                return {
                    'status': 0,
                    'token': t.token,
                    'message': 'Success!',
                    'subscribe': res,
                    'app_server' : query_server
                }
            else:
                return {
                    'status': 1,
                    'message': 'login assgin server failed due to unknown reason'
                }                
        else:
            return {
                'status': 1,
                'message': 'No such user or password error'
            }

    @__auth
    def logout(self, token, *args):
        if args:
            return {
                'status': 1,
                'message': 'Usage: logout <user>'
            }
        query = Chat_group.select(Chat_group.group_name).where(Chat_group.member == token.owner)
        res = []
        for group in query:
            res.append(group.group_name)  
        token.delete_instance()
        change = App_server.get(user=token.owner)
        change.delete_instance()
        return {
            'status': 0,
            'message': 'Bye!',
            'user' : token.owner.username,
            'unsubscribe': res,
        }


    @__auth
    def print_db(self,token, action = None, *args):    
        job = ['user', 'invite', 'friend' , 'post' , 'token' , 'chat_group']
        if action in job:
            if action == job[0]:
                user = User.select()
                for i in user:
                    print(str(i.username) + " " + str(i.password))
            elif action == job[1]:
                invite = Invitation.select()
                for i in invite:
                    print(str(i.inviter.username) + " " + str(i.invitee.username))                
            elif action == job[2]:
                friend = Friend.select()
                for i in friend:
                    print(str(i.user.username) + " " + str(i.friend.username))
            elif action == job[3]:
                post = Post.select()
                for i in post:
                    print(str(i.user.username) + " " + str(i.message))
            elif action == job[4]:
                token = Token.select()
                for i in token:
                    print(str(i.owner.username) + " " + str(i.token))
            elif action == job[5]:
                chat_group = Chat_group.select()
                for i in chat_group:
                    print(str(i.member.username) + " " + str(i.group_name))
            print("-------------------------------------------------")
        return {
            'status': 0,     
        } 

class Server(object):
    def __init__(self, ip, port):
        try:
            socket.inet_aton(ip)
            if 0 < int(port) < 65535:
                self.ip = ip
                self.port = int(port)
            else:
                raise Exception('Port value should between 1~65535')
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.db = DBControl()
        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    def run(self):
        self.sock.bind((self.ip, self.port))
        self.sock.listen(100)
        #socket.setdefaulttimeout(0.1)
        while True:
            try:
                conn, addr = self.sock.accept()
                with conn:
                    cmd = conn.recv(4096).decode()
                    resp = self.__process_command(cmd)
                    conn.send(resp.encode())
            except Exception as e:
                print(e, file=sys.stderr)

    def __process_command(self, cmd):
        command = cmd.split()
        if len(command) > 0:
            command_exec = getattr(self.db, command[0].replace('-', '_'), None)
            if command_exec:
                return json.dumps(command_exec(*command[1:]))
        return self.__command_not_found(command[0])

    def __command_not_found(self, cmd):
        return json.dumps({
            'status': 1,
            'message': 'Unknown command {}'.format(cmd)
        })


def launch_server(ip, port):
    c = Server(ip, port)
    c.run()

if __name__ == '__main__':
    if sys.argv[1] and sys.argv[2]:
        launch_server(sys.argv[1], sys.argv[2])
