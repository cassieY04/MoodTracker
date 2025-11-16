users = {}

class UserManager:
    @staticmethod
    def user_exists(username):
        return username in users
    
    @staticmethod
    def add_user(username, user_data):
        users[username] = user_data
    
    @staticmethod
    def get_user(username):
        return users.get(username)
    
    @staticmethod
    def update_user(username, user_data):
        if username in users:
            users[username].update(user_data)
    
    @staticmethod
    def delete_user(username):
        if username in users:
            del users[username]