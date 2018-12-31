import sys
import socket
import json
import os
import stomp
class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)
    def on_message(self, headers, message):
        print(message)
class Client(object):
    def __init__(self, ip, port):
        try:
            socket.inet_aton(ip)
            if 0 < int(port) < 65535:
                self.ip = ip
                self.port = int(port)
            else:
                raise Exception('Port value should between 1~65535')
            self.cookie = {}
            self.conn = stomp.Connection()
            self.conn.set_listener('', MyListener())
            self.conn.start()
            self.conn.connect('admin', 'password', wait=True)            
        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    def run(self):
        while True:
            cmd = sys.stdin.readline()
            if cmd == 'exit' + os.linesep:
                return
            if cmd != os.linesep:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((self.ip, self.port))
                        cmd = self.__attach_token(cmd)
                        s.send(cmd.encode())
                        resp = s.recv(4096).decode()
                        self.__show_result(json.loads(resp), cmd)
                except Exception as e:
                    print(e, file=sys.stderr)

    def __show_result(self, resp, cmd=None):
        if 'message' in resp:
            print(resp['message'])

        if 'invite' in resp:
            if len(resp['invite']) > 0:
                for l in resp['invite']:
                    print(l)
            else:
                print('No invitations')

        if 'friend' in resp:
            if len(resp['friend']) > 0:
                for l in resp['friend']:
                    print(l)
            else:
                print('No friends')

        if 'post' in resp:
            if len(resp['post']) > 0:
                for p in resp['post']:
                    print('{}: {}'.format(p['id'], p['message']))
            else:
                print('No posts') 
        if 'group' in resp:
            if len(resp['group']) > 0:
                for g in resp['group']:
                    print(g)
            else:
                print('No groups')
        if cmd:
            command = cmd.split()
            if resp['status'] == 0 and command[0] == 'login':
                if command[1] in self.cookie:
                    if resp['token'] != self.cookie[command[1]] :
                        self.cookie[command[1]] = resp['token']
                        self.__subscribe_channel(command[1], resp['token'], resp['subscribe'])
                else:
                    self.cookie[command[1]] = resp['token']
                    self.__subscribe_channel(command[1], resp['token'], resp['subscribe'])
            elif resp['status'] == 0 and command[0] == 'logout':
                self.__unsubscribe_channel(resp['user'], command[1], resp['unsubscribe'])
            elif resp['status'] == 0 and command[0] == 'create-group':
                self.__subscribe_group_during_login(command)
            elif resp['status'] == 0 and command[0] == 'join-group':
                self.__subscribe_group_during_login(command)
            elif resp['status'] == 0 and command[0] == 'delete':
                self.__unsubscribe_channel(resp['user'], command[1], resp['unsubscribe'])
    def __attach_token(self, cmd=None):
        if cmd:
            command = cmd.split()
            if len(command) > 1:
                if command[0] != 'register' and command[0] != 'login':
                    if command[1] in self.cookie:
                        command[1] = self.cookie[command[1]]
                    else:
                        command.pop(1)
            return ' '.join(command)
        else:
            return cmd
    def __subscribe_channel(self, user, token, subscribe_to):
        self.conn.subscribe(destination='/topic/friend/' + str(user), id = token)
        for i in subscribe_to:
            self.conn.subscribe(destination='/topic/group/' + str(i), id = str(token)+str(i))
    def __unsubscribe_channel(self, user, token, unsubscribe_to):
        self.conn.unsubscribe(destination='/topic/friend/' + str(user), id = token)
        for i in unsubscribe_to:
            self.conn.unsubscribe(destination='/topic/group/' + str(i), id = str(token)+str(i))
    def __subscribe_group_during_login(self, cmd):
        self.conn.subscribe(destination='/topic/group/' + str(cmd[2]), id = str(cmd[1])+str(cmd[2]))

    


def launch_client(ip, port):
    c = Client(ip, port)
    c.run()

if __name__ == '__main__':
    if len(sys.argv) == 3:
        launch_client(sys.argv[1], sys.argv[2])
    else:
        print('Usage: python3 {} IP PORT'.format(sys.argv[0]))
