import socketserver
import json
import datetime
from peewee import *
import uuid
import sys

db = SqliteDatabase('my_app.db')

class BaseModel(Model):
	class Meta:
		database = db

class User(BaseModel):
	user_id = CharField(unique=False)
	password = CharField(unique=False)
	login = BooleanField(default=False)
	token = CharField(unique=True)
	created_date = DateTimeField(default=datetime.datetime.now)

class pending_friendship(BaseModel):
	sent_from = CharField(unique=False)
	to_whom = CharField(unique=False)
	accept = BooleanField(default=False)
	sent_date = DateTimeField(default=datetime.datetime.now)

class friendship(BaseModel):
	sent_from = CharField(unique=False)
	to_whom = CharField(unique=False)
	anniversary_date = DateTimeField(default=datetime.datetime.now)
class post_info(BaseModel):
	user_id = CharField(unique=False)
	message = TextField()
	post_date = DateTimeField(default=datetime.datetime.now)

def register(command):
	status = 0
	message = ""
	if(len(command) != 3):
		status = 1
		message = "Usage: register <id> <password>"
	else:	
		query = User.select().where(User.user_id == command[1])
		if(len(query) > 0):
			status = 1
			message = str(command[1])+" is already used"
	if(status == 0):
		User.create(user_id = command[1] ,token = command[1], password = command[2])
		message = "Success!"
	response = { 'status': status, 'message': message }
	return response
def login(command):
	status = 0
	message = "Success!"
	token = ""
	if(len(command) != 3):
		status = 1
		message = "Usage: login <id> <password>"
	else:
		query = User.select().where(User.user_id == command[1])
		if(len(query) == 0):
			status = 1
			message = "No such user or password error"
		else:
			if(query[0].password != command[2]):
				status = 1
				message = "No such user or password error"
			else:
				token = uuid.uuid3(uuid.NAMESPACE_DNS, str(query[0].user_id)+str(datetime.datetime.time(datetime.datetime.now())))
				query = (User.update({User.token: token, User.login: True}).where(User.user_id == command[1]))
				query.execute()
	if(status == 1):
		response = { 'status': status, 'message': message }
	else:
		response = { 'status': status, 'token': str(token), 'message': message }
	return response
def logout(command):
	status = 0
	message = "Bye!"
	if(len(command) > 2):
		status = 1
		message = "Usage: logout <user>"
	elif(len(command) < 2):
		status = 1
		message = "Not login yet"		
	else:
		query = User.select().where((User.token == command[1]) & (User.login == True))
		if(len(query) == 0):
			status = 1
			message = "Not login yet"
		else:
			update = (User.update({User.token: "",User.login : False}).where(User.token == command[1]))
			update.execute()
	response = { 'status': status, 'message': message }
	return response
def list_user():
	print("list user")
	query = User.select()
	for user in query:
		print(str(user.user_id) +"  "+ str(user.token) + " " + str(user.login))
def list_pending():
	print("list pending")
	query = pending_friendship.select()
	for i in query:
		print(str(i.sent_from) + " " + str(i.to_whom) + " " + str(i.accept))
def list_friendship():
	print("list friendship")
	query = friendship.select()
	for i in query:
		print(str(i.sent_from) + " " + str(i.to_whom) + " " + str(i.anniversary_date))
def list_post():
	print("list post")
	query = post_info.select()
	for i in query:
		print(str(i.user_id) + " " + str(i.message))
def delete(command):
	status = 0
	message = "Success!"
	if(len(command) > 2):
		status = 1
		message = "Usage: delete <user>"
	elif(len(command) < 2):
		status = 1
		message = "Not login yet"		
	else:
		user = User.select().where(User.token == command[1])
		if(len(user) == 0):
			status = 1
			message = "Not login yet"
		else:
			delete_pending = (pending_friendship.delete().where((pending_friendship.sent_from == user[0].user_id) | (pending_friendship.to_whom == user[0].user_id)))
			delete_friendship = (friendship.delete().where((friendship.sent_from == user[0].user_id) | (friendship.to_whom == user[0].user_id)))
			delete_post = (post_info.delete().where(post_info.user_id == user[0].user_id))
			delete_user = (User.delete().where(User.token == command[1]))
			delete_pending.execute()
			delete_friendship.execute()
			delete_post.execute()
			delete_user.execute()
	response = { 'status': status, 'message': message }
	return response

def invite(command):
	status = 0
	message = "Success!"
	token = ""
	if(len(command) <3):
		status = 1
		message = "Not login yet"
	elif(len(command) > 3):
		status = 1
		message = "Usage: invite <user> <id>"
	else:
		sent_from = User.select().where((User.token == command[1]) & (User.login == True))
		if(len(sent_from) == 0):
			status = 1
			message = "Not login yet"
		else:
			to_whom = User.select().where(User.user_id == command[2])
			if(len(to_whom) == 0):
				status = 1
				message = str(command[2]) + " does not exist"
			else:
				if(to_whom[0].token == command[1]):
					status = 1
					message = "You cannot invite yourself"
				else:
					check_already_invited = pending_friendship.select().where((pending_friendship.sent_from == sent_from[0].user_id) & (pending_friendship.to_whom == command[2]))
					check_has_invited = pending_friendship.select().where((pending_friendship.sent_from == command[2]) & (pending_friendship.to_whom == sent_from[0].user_id)) 
					if(len(check_already_invited) > 0):
						if(check_already_invited[0].accept == True):
							status = 1
							message = str(command[2])+" is already your friend"
						else:
							status = 1
							message = "Already invited"
					else:
						if(len(check_has_invited) > 0):
							if(check_has_invited[0].accept == True):
								status = 1
								message = str(command[2])+" is already your friend"
							else:
								status = 1
								message = str(check_has_invited[0].sent_from) + " has invited you"
						else:
							add_invite = pending_friendship.create(sent_from = sent_from[0].user_id ,to_whom = command[2])
	response = { 'status': status, 'message': message }
	return response	
def list_invite(command):
	status = 0
	message = ""
	invite_list = []
	if(len(command)<2):
		status = 1
		message = "Not login yet"
		response = { 'status': status, 'message': message }
	elif(len(command) > 2):
		status = 1
		message = "Usage: list-invite <user>"
		response = { 'status': status, 'message': message }
	else:
		user = User.select().where(User.token == command[1])
		query = pending_friendship.select().where((pending_friendship.to_whom == user[0].user_id) & (pending_friendship.accept == False))
		for i in query:
			invite_list.append(i.sent_from)
		response = { 'status': status, 'invite': invite_list }

	return response
def accept_invite(command):
	status = 0
	message = "Success!"
	if(len(command) <3):
		status = 1
		message = "Not login yet"
	elif(len(command) > 3):
		status = 1
		message = "Usage: accept-invite <user> <id>"
	else:
		user = User.select().where(User.token == command[1])
		query = pending_friendship.select().where((pending_friendship.to_whom == user[0].user_id) & (pending_friendship.sent_from == command[2]) & (pending_friendship.accept == False))
		if(len(query) == 0):
			status = 1
			message = str(command[2]) + " did not invite you"
		else:
			update_pending = (pending_friendship.update({pending_friendship.accept : True}).where((pending_friendship.to_whom == user[0].user_id) & (pending_friendship.sent_from == command[2])))
			update_pending.execute()
			update_friendship = friendship.create(sent_from =command[2] , to_whom = user[0].user_id )

	response = { 'status': status, 'message': message }
	return response
def list_friend(command):
	status = 0
	message = ""
	friend_list = []
	if(len(command)<2):
		status = 1
		message = "Not login yet"
		response = { 'status': status, 'message': message }
	elif(len(command) > 2):
		status = 1
		message = "Usage: list-friend <user>"
		response = { 'status': status, 'message': message }
	else:
		user = User.select().where(User.token == command[1])
		query = friendship.select().where((friendship.to_whom == user[0].user_id) | (friendship.sent_from == user[0].user_id))
		for i in query:
			if(i.sent_from == user[0].user_id):
				friend_list.append(i.to_whom)
			else:
				friend_list.append(i.sent_from)
		response = { 'status': status, 'friend': friend_list }
	return response
def post(command):
	status = 0
	message = "Success!"
	if(len(command) == 1):
		status = 1
		message = "Not login yet"
	elif(len(command) == 2):
		user = User.select().where(User.token == command[1] & User.login == True)
		if(len(user) == 0):
			status = 1
			message = "Not login yet"
		else:
			status = 1
			message = "Usage: post <user> <message>"
	else:
		user = User.select().where((User.token == command[1]) & (User.login == True))
		if(len(user) == 0):
			status = 1
			message = "Not login yet"
		else:
			data = command
			data.pop(0)
			data.pop(0)
			space = " "
			my_poss = space.join( data );
			share = post_info.create(user_id =user[0].user_id , message = str(my_poss) )
	response = { 'status': status, 'message': message }
	return response
def receive_post(command):
	status = 0
	message = ""
	friend_list = []
	post_list = []
	if(len(command)<2):
		status = 1
		message = "Not login yet"
		response = { 'status': status, 'message': message }
	elif(len(command) > 2):
		status = 1
		message = "Usage: receive-post <user>"
		response = { 'status': status, 'message': message }
	else:
		user = User.select().where((User.token == command[1]) & (User.login == True))
		if(len(user) == 0):
			status = 1
			message = message = "Not login yet"
			response = { 'status': status, 'message': message }
		else:
			find_friend = friendship.select().where((friendship.to_whom == user[0].user_id) | (friendship.sent_from == user[0].user_id))
			for i in find_friend:
				if(i.sent_from == user[0].user_id):
					friend_list.append(i.to_whom)
				else:
					friend_list.append(i.sent_from)
			for i in friend_list:
				query_friend_post = post_info.select().where((post_info.user_id == i))
				for j in query_friend_post:
					post_list.append({'id': j.user_id, 'message' : j.message})
			response = { 'status': status, 'post': post_list }
	return response





class MyTCPHandler(socketserver.BaseRequestHandler):

	"""
	The RequestHandler class for our server.

	It is instantiated once per connection to the server, and must
	override the handle() method to implement communication to the
	client.
	"""
	#function
	#def register(command):	
	def handle(self):
		# self.request is the TCP socket connected to the client
		self.data = self.request.recv(4096).strip()
		print("{} wrote:".format(self.client_address[0]))
		print(self.data.decode())
		re_data = self.data.decode()
		command = re_data.split(" ")
		tmp = {}
		if(command[0] == "register"):
			tmp = register(command)
		elif(command[0] == "login"):
			tmp = login(command)
		elif(command[0] == "logout"):
			tmp = logout(command)
		elif(command[0] == "delete"):
			tmp = delete(command)
		elif(command[0] == "invite"):
			tmp = invite(command)
		elif(command[0] == "list-invite"):
			tmp = list_invite(command)
		elif(command[0] == "accept-invite"):
			tmp = accept_invite(command)
		elif(command[0] == "list-friend"):
			tmp = list_friend(command)
		elif(command[0] == "post"):
			tmp = post(command)
		elif(command[0] == "receive-post"):
			tmp = receive_post(command)
		else:
			tmp = {'status' : 1,'message' : "Unknown command " + str(command[0])}
		response = json.dumps(tmp)
		# just send back the same data, but upper-cased
		self.request.sendall(response.encode())

if __name__ == "__main__":
	HOST, PORT = sys.argv[1], int(sys.argv[2])
	db.create_tables([User, pending_friendship, friendship, post_info])
	# Create the server, binding to localhost on port 9999
	server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)

	# Activate the server; this will keep running until you
	# interrupt the program with Ctrl-C
	server.serve_forever()
