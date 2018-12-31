#-*- coding: utf-8 -*-
import socket
import sys
import json
user_info = {}
#HOST = '140.113.207.51'    # The remote host
#PORT = 8008              # The same port as used by the server
HOST = sys.argv[1]    # The remote host
PORT = sys.argv[2]              # The same port as used by the server
def register(command,data):
    if(int(data['status']) == 0):
        user_info[command[1]] = ""
        print(data['message'])
    else :
        print(data['message'])
    
def login(command,data):
    if(int(data['status']) == 0):
        user_info[command[1]] = data['token']
        print(data['message'])
    else :
        print(data['message'])
def delete(command,data):
    if(int(data['status']) == 0):
        del user_info[command[1]]
        print(data['message'])
    else :
        print(data['message'])
def logout(command,data):
    if(int(data['status']) == 0):
        user_info[command[1]] = ""
        print(data['message'])
    else :
        print(data['message'])    
def invite(command,data):
    if(int(data['status']) == 0):
        print(data['message'])
    else :
        print(data['message']) 
def list_invite(command,data):
    if(int(data['status']) == 0):
        if(len(data['invite']) > 0):
            for i in data['invite'] :
                print(i)
        else:
            print("​\bNo invitations​")
    else:
        print(data['message'])
def accept_invite(command,data):
    if(int(data['status']) == 0):
        print(data['message'])
    else :
        print(data['message']) 
def list_friend(command,data):
    if(int(data['status']) == 0):
        if(len(data['friend']) > 0):
            for i in data['friend'] :
                print(i)
        else:
            print("​\bNo friends​")
    else:
        print(data['message'])
def post(command,data):
    if(int(data['status']) == 0):
        print(data['message'])
    else :
        print(data['message']) 
def receive_post(command, data):
    if(int(data['status']) == 0):
        if(len(data['post']) > 0):
            for i in data['post'] :
                print(i['id']+': '+i['message'])
        else:
            print("​\bNo posts​")
    else:
        print(data['message'])   
def other(command, data):
    print(data['message'])     


while True:
    command = input()
    command_send = command
    s = None
    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except OSError as msg:
            s = None
            continue
        try:
            s.connect(sa)
        except OSError as msg:
            s.close()
            s = None
            continue
        break
    if s is None:
        print('could not open socket')
        sys.exit(1)
    with s:
        command = command.split(" ")
        if(command[0] == "register"):
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            register(command,data)
        elif(command[0] == "login"):
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            login(command,data)
        elif(command[0] == "delete"):
            if(len(command) > 1):
                if(command[1] in user_info and user_info[command[1]] != ""):
                    command_send = command_send.replace( command[1], str(user_info[command[1]]) )
                elif(command[1] in user_info):
                    command_send = command_send.replace( command[1], "" )
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            delete(command, data)  
        elif(command[0] == "logout"):
            if(len(command) > 1):
                if(command[1] in user_info and user_info[command[1]] != ""):
                    command_send = command_send.replace( command[1], str(user_info[command[1]]) )
                elif(command[1] in user_info):
                    command_send = command_send.replace( command[1], "" )
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            logout(command, data)
        elif(command[0] == "invite"):
            if(len(command) > 1):
                if(command[1] in user_info and user_info[command[1]] != ""):
                    command_send = command_send.replace( command[1], str(user_info[command[1]]) ,1)
                elif(command[1] in user_info):
                    command_send = command_send.replace( command[1], "" )
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            invite(command, data)     
        elif(command[0] == "list-invite"):
            if(len(command) > 1):
                if(command[1] in user_info and user_info[command[1]] != ""):
                    command_send = command_send.replace( command[1], str(user_info[command[1]]) ,1)
                elif(command[1] in user_info):
                    command_send = command_send.replace( command[1], "" )
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            list_invite(command, data)
        elif(command[0] == "accept-invite"):
            if(len(command) > 1):
                if(command[1] in user_info and user_info[command[1]] != ""):
                    command_send = command_send.replace( command[1], str(user_info[command[1]]) ,1)
                elif(command[1] in user_info):
                    command_send = command_send.replace( command[1], "" )
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            accept_invite(command, data) 
        elif(command[0] == "list-friend"):
            if(len(command) > 1):
                if(command[1] in user_info and user_info[command[1]] != ""):
                    command_send = command_send.replace( command[1], str(user_info[command[1]]) ,1)
                elif(command[1] in user_info):
                    command_send = command_send.replace( command[1], "" )
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            list_friend(command, data)   
        elif(command[0] == "post"):
            if(len(command) > 1):
                if(command[1] in user_info and user_info[command[1]] != ""):
                    command_send = command_send.replace( command[1], str(user_info[command[1]]) ,1)
                elif(command[1] in user_info):
                    command_send = command_send.replace( command[1], "" )
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            post(command, data)    
        elif(command[0] == "receive-post"):
            if(len(command) > 1):
                if(command[1] in user_info and user_info[command[1]] != ""):
                    command_send = command_send.replace( command[1], str(user_info[command[1]]) ,1)
                elif(command[1] in user_info):
                    command_send = command_send.replace( command[1], "" )
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            receive_post(command, data)      
        elif(command[0] == "exit"):
            for i in user_info:
                i = ""   
            break;
        else:
            command_send = command_send.encode("UTF-8")
            s.sendall(command_send)
            data = json.loads(s.recv(1024).decode("UTF-8"))
            other(command, data)  
        #print(data['message'])

