from flask import current_app


def get_msg_manager():
    return current_app.config['MSG_MANAGER']


class MessageManager:

    def __init__(self):
        self.messages = []

    def append_error(self, ex):
        new_error = ("error" + str(len(self.messages)), str(ex), 'err')
        self.messages.append(new_error)
        return new_error