import sys
import socket
from model import *
import json
import uuid
import time
import stomp
import boto3
from model import *
from peewee import *
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
        ImageId="ami-0bb4c03e5d990c0ce", 
        InstanceType = "t2.micro",  
        SecurityGroupIds=['launch-wizard-1'],
        MinCount=1,
        MaxCount=1,
        KeyName='qq_key',
        UserData=user_data

    )
    instance[0].wait_until_running()
    instance_collection = ec2.instances.filter(InstanceIds=[instance[0].instance_id])
    for i in instance_collection:
        return (i.public_ip_address, instance[0].instance_id)
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
        find_ip = App_server.get_or_none(App_server.user == token.owner) 
        query_server = App_server.select(App_server.server_ip, App_server.instance_id).where(App_server.server_ip == find_ip.server_ip).having(fn.Count(App_server.user) < 2)
        if (len(query_server) > 0):
            ec2.instances.filter(InstanceIds=[query_server[0].instance_id]).terminate() 
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
            instance_id = ""
            server_ip = ""                
            query_server = App_server.select(App_server.server_ip, App_server.instance_id).group_by(App_server.server_ip).having(fn.Count(App_server.user) < 10)
            if (len(query_server) == 0):
                server_ip, instance_id = createInstance()
            else:
                server_ip = query_server[0].server_ip
                instance_id = query_server[0].instance_id
            record = App_server.create(user = t.owner, server_ip = server_ip, instance_id = instance_id)
            if record:
                return {
                    'status': 0,
                    'token': t.token,
                    'message': 'Success!',
                    'subscribe': res,
                    'app_server' : server_ip
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
        find_ip = App_server.get_or_none(App_server.user == token.owner) 
        query_server = App_server.select(App_server.server_ip, App_server.instance_id).where(App_server.server_ip == find_ip.server_ip).having(fn.Count(App_server.user) < 2)
        if (len(query_server) > 0):
            ec2.instances.filter(InstanceIds=[query_server[0].instance_id]).terminate()
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
    def invite(self, token, username=None, *args):
        if not username or args:
            return {
                'status': 1,
                'message': 'Usage: invite <user> <id>'
            }
        if username == token.owner.username:
            return {
                'status': 1,
                'message': 'You cannot invite yourself'
            }
        friend = User.get_or_none(User.username == username)
        if friend:
            res1 = Friend.get_or_none((Friend.user == token.owner) & (Friend.friend == friend))
            res2 = Friend.get_or_none((Friend.friend == token.owner) & (Friend.user == friend))
            if res1 or res2:
                return {
                    'status': 1,
                    'message': '{} is already your friend'.format(username)
                }
            else:
                invite1 = Invitation.get_or_none((Invitation.inviter == token.owner) & (Invitation.invitee == friend))
                invite2 = Invitation.get_or_none((Invitation.inviter == friend) & (Invitation.invitee == token.owner))
                if invite1:
                    return {
                        'status': 1,
                        'message': 'Already invited'
                    }
                elif invite2:
                    return {
                        'status': 1,
                        'message': '{} has invited you'.format(username)
                    }
                else:
                    Invitation.create(inviter=token.owner, invitee=friend)
                    return {
                        'status': 0,
                        'message': 'Success!'
                    }
        else:
            return {
                'status': 1,
                'message': '{} does not exist'.format(username)
            }
        pass

    @__auth
    def list_invite(self, token, *args):
        if args:
            return {
                'status': 1,
                'message': 'Usage: list-invite <user>'
            }
        res = Invitation.select().where(Invitation.invitee == token.owner)
        invite = []
        for r in res:
            invite.append(r.inviter.username)
        return {
            'status': 0,
            'invite': invite
        }

    @__auth
    def accept_invite(self, token, username=None, *args):
        if not username or args:
            return {
                'status': 1,
                'message': 'Usage: accept-invite <user> <id>'
            }
        inviter = User.get_or_none(User.username == username)
        invite = Invitation.get_or_none((Invitation.inviter == inviter) & (Invitation.invitee == token.owner))
        if invite:
            Friend.create(user=token.owner, friend=inviter)
            invite.delete_instance()
            return {
                'status': 0,
                'message': 'Success!'
            }
        else:
            return {
                'status': 1,
                'message': '{} did not invite you'.format(username)
            }
        pass

    @__auth
    def list_friend(self, token, *args):
        if args:
            return {
                'status': 1,
                'message': 'Usage: list-friend <user>'
            }
        friends = Friend.select().where((Friend.user == token.owner) | (Friend.friend == token.owner))
        res = []
        for f in friends:
            if f.user == token.owner:
                res.append(f.friend.username)
            else:
                res.append(f.user.username)
        return {
            'status': 0,
            'friend': res
        }

    @__auth
    def post(self, token, *args):
        if len(args) <= 0:
            return {
                'status': 1,
                'message': 'Usage: post <user> <message>'
            }
        Post.create(user=token.owner, message=' '.join(args))
        return {
            'status': 0,
            'message': 'Success!'
        }

    @__auth
    def receive_post(self, token, *args):
        if args:
            return {
                'status': 1,
                'message': 'Usage: receive-post <user>'
            }
        res = Post.select().where(Post.user != token.owner).join(Friend, on=((Post.user == Friend.user) | (Post.user == Friend.friend))).where((Friend.user == token.owner) | (Friend.friend == token.owner))
        post = []
        for r in res:
            post.append({
                'id': r.user.username,
                'message': r.message
            })
        return {
            'status': 0,
            'post': post
        }

    @__auth
    def send(self, token, username=None, *args):
        if not username or len(args) <= 0:
            return {
                'status': 1,
                'message': 'Usage: send <user> <friend> <message>'
            }
        user_exist = User.get_or_none(User.username == username)
        if user_exist:
            friend1 = Friend.get_or_none((Friend.user == token.owner) & (Friend.friend == user_exist))
            friend2 = Friend.get_or_none((Friend.friend == token.owner) & (Friend.user == user_exist)) 
            if friend1 or friend2 :
                friend_online = Token.get_or_none(Token.owner == user_exist)
                if friend_online:
                    message = "<<<" + str(token.owner.username) + "->" + str(username) + ": " +  str(' '.join(args)) + ">>>"
                    connect_to_mq.send(body=message, destination='/topic/friend/'+str(username))
                    return {
                        'status': 0,
                        'message': 'Success!'
                    }                    
                else:
                    return {
                        'status': 1,
                        'message': '{} is not online'.format(username)
                    }      
            else:
                return {
                    'status': 1,
                    'message': '{} is not your friend'.format(username)
                }                 
        else:
            return {
                'status': 1,
                'message': 'No such user exist'
            }

    @__auth
    def create_group(self, token, group_name = None, *args):
        if args or not group_name:
            return {
                'status': 1,
                'message': 'Usage: create-group <user> <group>'
            }
        group_exit = Chat_group.get_or_none(Chat_group.group_name == group_name)
        if group_exit:
            return {
                'status': 1,
                'message': '{} already exist'.format(group_name)           
            }
        else:
            res = Chat_group.create(member = token.owner, group_name = group_name)
            if res:
                return {
                    'status': 0,
                    'message': 'Success!'           
                }
            else:
                return {
                    'status': 1,
                    'message': 'create group failed due to unknown reason'                
                }

    @__auth
    def list_group(self, token, *args):
        if args:
            return {
                'status': 1,
                'message': 'Usage: list-group <user>'
            } 
        query = Chat_group.select(Chat_group.group_name).distinct()
        res = []
        for group in query:
            res.append(group.group_name)
        return {
            'status': 0,
            'group' : res         
        }

    @__auth
    def join_group(self, token, group_name = None, *args):
        if args or not group_name:
            return {
                'status': 1,
                'message': 'Usage: join-group <user> <group>'
            }
        group_exit = Chat_group.get_or_none(Chat_group.group_name == group_name)
        if group_exit:
            already_in = Chat_group.get_or_none((Chat_group.group_name == group_name) & (Chat_group.member == token.owner))
            if already_in:
                return {
                    'status': 1,
                    'message': 'Already a member of {}'.format(group_name)                    
                }
            else :
                res = Chat_group.create(member = token.owner, group_name = group_name)
                if res:
                    return {
                        'status': 0,
                        'message': 'Success!'             
                    }
                else:
                    return {
                        'status': 1,
                        'message': 'create group failed due to unknown reason'                
                    }
        else:
            return {
                'status': 1,
                'message': '{} does not exist'.format(group_name)             
            }
    @__auth
    def list_joined(self, token, *args):
        if args:
            return {
                'status': 1,
                'message': 'Usage: list-joined <user>'
            } 
        query = Chat_group.select(Chat_group.group_name).where(Chat_group.member == token.owner)
        res = []
        for group in query:
            res.append(group.group_name)
        return {
            'status': 0,
            'group' : res         
        }

    @__auth
    def send_group(self, token, group_name=None, *args):
        if not group_name or len(args) <= 0:
            return {
                'status': 1,
                'message': 'Usage: send-group <user> <group> <message>'
            }
        group_exit = Chat_group.get_or_none(Chat_group.group_name == group_name)
        if group_exit:
            already_in = Chat_group.get_or_none((Chat_group.group_name == group_name) & (Chat_group.member == token.owner))
            if already_in:
                message = "<<<" + str(token.owner.username) + "->" + "GROUP<" + str(group_name) + ">: " +  str(' '.join(args)) + ">>>"
                connect_to_mq.send(body=message, destination='/topic/group/'+str(group_name))
                return {
                    'status': 0,
                    'message': 'Success!'      
                }                
            else:
                return {
                    'status': 1,
                    'message': 'You are not the member of {}'.format(group_name)                    
                }
        else:
            return {
                'status': 1,
                'message': 'No such group exist'             
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
                    print(cmd)
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
