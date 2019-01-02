from peewee import *


db = MySQLDatabase('tkche870302', user='tkche870302', password='Mq870302',host='database.cld8fxrg0zdy.us-east-2.rds.amazonaws.com', port=3306)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()


class Invitation(BaseModel):
    inviter = ForeignKeyField(User, on_delete='CASCADE')
    invitee = ForeignKeyField(User, on_delete='CASCADE')


class Friend(BaseModel):
    user = ForeignKeyField(User, on_delete='CASCADE')
    friend = ForeignKeyField(User, on_delete='CASCADE')


class Post(BaseModel):
    user = ForeignKeyField(User, on_delete='CASCADE')
    message = CharField()


class Follow(BaseModel):
    follower = ForeignKeyField(User, on_delete='CASCADE')
    followee = ForeignKeyField(User, on_delete='CASCADE')


class Token(BaseModel):
    token = CharField(unique=True)
    owner = ForeignKeyField(User, on_delete='CASCADE')

class Chat_group(BaseModel):
    group_name = CharField(unique=False)
    member = ForeignKeyField(User, on_delete='CASCADE')
class App_server(BaseModel):
    user = ForeignKeyField(User, on_delete='CASCADE')
    server_ip = CharField(unique=False)
    instance_id = CharField(unique=False)



if __name__ == '__main__':
    db.connect()
    db.create_tables([User, Invitation, Friend, Post, Follow, Token, Chat_group, App_server])
    #query_server = App_server.select(App_server.server_ip).group_by(App_server.server_ip).having(fn.Count(App_server.user) < 10)
    #t = Token.get_or_none(Token.token == "2dab19ee-dc76-4844-8e4b-c002eeebff8f")
    #find_ip = App_server.get_or_none(App_server.user == t.owner) 
    query_server = App_server.select(App_server.server_ip, App_server.instance_id).group_by(App_server.server_ip).having(fn.Count(App_server.user) < 10)
    print(len(query_server))

