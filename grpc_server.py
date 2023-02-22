from concurrent import futures
import logging
from collections import defaultdict
from uuid import uuid4
import binascii
import os
import re

from datetime import timezone
import datetime

import grpc
import chat_pb2
import chat_pb2_grpc
import threading as mp


class ChatServer(chat_pb2_grpc.ChatServerServicer):
    def __init__(self) -> None:
        super().__init__()
        self.user_inbox = defaultdict(lambda: [])
        
        # format of metadata store
        # key - username (must be unique)
        # per value entry (password, name)
        self.user_metadata_store = {}
        self.token_length = 15
        
        # token hub keys are usernames and the values are token, timestamp pairs
        self.token_hub = {}
        
        # keeping track of time by standardizing to UTC
        self.utc_time_gen = datetime.datetime
        
        # user metadata lock
        self.metadata_lock = mp.Lock()
        
        # inbox lock
        self.inbox_lock = mp.Lock()
        
    def ValidatePassword(self, password):
        """
        Validates a password to ensure that it is a string.

        Args:
            password (str): The password to validate.

        Returns:
            int: Returns 0 if the password is a string, or -1 if it is not.
        """
        if type(password) != str:
            return -1
        else:
            return 0
        
    def GenerateToken(self):
        """
        Generates a token for authenticating user requests to a chat server.

        Returns:
            str: A token that can be used to authenticate user requests.
        """
        
        token = os.urandom(self.token_length)
        return binascii.hexlify(token).decode()
    
    def ValidateToken(self, username: str, token: str) -> int:
        """
        Validates a user token and checks if it has expired.

        Args:
            username (str): The username associated with the token.
            token (str): The token to validate.

        Returns:
            int: Returns 0 if the token is valid and has not expired, 
            or -1 if it is invalid or has expired.
        """
        
        with self.metadata_lock:
            if username not in self.token_hub.keys():
                return -1
            
            stored_token, timestamp = self.token_hub[username]
            
            if stored_token != token:
                return -1
            
            duration = self.utc_time_gen.now().timestamp() - timestamp
            duration_in_hr = duration / 3600
            
            if duration_in_hr > 1.0:
                return -1
            
            return 0

    def SendMessage(self, request, context) -> chat_pb2.MessageReply:
        """
        Receives a request object from the user 
        and stores the message in the correct recipient's inbox.

        Args:
            request (obj): A struct representing a message sent by a user, 
            containing the message content,
            recipient username, and authentication token.

        Returns:
            chat_pb2.MessageReply: A message reply object containing 
            a version number and error code, if applicable.

        The function first parses the request message from struct 
        using the `MessageRequest` object. It then validates the authentication token 
        and recipient username using the `ValidateToken` function. If the validation
        fails, the function returns a `MessageReply` object with an appropriate error code.

        If the authentication token and recipient username are valid, 
        the function appends the message to the recipient's
        inbox and returns a `MessageReply` object with a success code.

        The function uses the `inbox_lock` to protect access 
        to the inbox dictionaries and ensures that the inbox for the
        recipient exists before attempting to append the message. 
        If the recipient does not exist, the function returns a
        `MessageReply` object with an error code indicating an invalid recipient.
        """
        
        token = request.auth_token
        username = request.username
        recipient = request.recipient_username
        if self.ValidateToken(username=username,
                              token=token) < 0:
            return chat_pb2.MessageReply(version=1,
                                         error_code="Invalid Token")
        
        message_string = request.message
        modified_string = f"[{username}]: {message_string}"
        
        with self.inbox_lock:
            if recipient not in self.user_inbox.keys():
                return chat_pb2.MessageReply(version=1,
                                            error_code="Invalid Recipient")
            self.user_inbox[recipient].append(modified_string)
            return chat_pb2.MessageReply(version=1, error_code="")
        
    
    def CheckInboxLength(self, username: str) -> int:
        """
        Return the length of the user's inbox for the given username.
        Protects metadata with locking.

        Args:
            username (str): A string representing the username of 
            the user whose inbox length needs to be checked.

        Returns:
            int: An integer representing the number 
            of messages in the user's inbox.
        """
        with self.inbox_lock:
            return len(self.user_inbox[username])

    def DeliverMessages(self, request, context) -> chat_pb2.RefreshReply:
        """
        Given a user request, 
        validate the request and deliver a set of messages to the user.

        Args:
            request (obj): A user request struct.

        Returns:
            chat_pb2.RefreshReply: A RefreshReply object containing 
            the messages and/or error code.


        This function validates the user request, 
        and if the request is valid, 
        it checks the user inbox for any new messages.
        If there are new messages, it returns a RefreshReply object 
        with the messages and an empty inbox.
        If there are no new messages, it returns a 
        RefreshReply object with an empty message and an error code.
        """
        # every client will end up running this
        while True:
            token = request.auth_token
            username = request.username
            if self.ValidateToken(username=username,
                                token=token) < 0:
                return chat_pb2.RefreshReply(version=1,
                                             error_code="Invalid Token")
            # Check if there are any new messages
            while self.CheckInboxLength(username=username) > 0:
                with self.inbox_lock:
                    msg = self.user_inbox[username].pop(0)
                
                # ended lock context before yield
                yield chat_pb2.RefreshReply(version=1, 
                                            error_code="",
                                            message=msg)

    def Login(self, request, context) -> chat_pb2.LoginReply:
        """
        Authenticate a user and generate a token for them to access the chat server.

        Args:
            request (obj): A request struct containing the LoginRequest message.

        Returns:
            chat_pb2.LoginReply: A message containing the authentication token 
            and user information, or an error message if the login failed.

        The function validates the given username 
        and password against the user metadata store,
        and generates a new token for 
        the user if the login is successful. 
        The token is stored in the token hub, 
        and returned to the user in the LoginReply message. 
        If the username or password is invalid, 
        an error message is returned instead.
        Note that the LoginRequest message is 
        deserialized from the `raw_bytes` string before processing, 
        and the LoginReply message is serialized before being returned.
        """
        # get the given username and do basic error checking
        username = request.username
        
        with self.metadata_lock:
            if username not in self.user_metadata_store.keys():
                return chat_pb2.LoginReply(
                                    error_code="ERROR Username Invalid",
                                    auth_token="",
                                    fullname="")
                
            # basic password match
            password = request.password
            if password != self.user_metadata_store[username][0]:
                return chat_pb2.LoginReply(
                                    error_code="ERROR Password Invalid",
                                    auth_token="",
                                    fullname="")
            
            # generate new token
            token = self.GenerateToken()
            timestamp = self.utc_time_gen.now().timestamp()
            
            # register token in token hub
            self.token_hub[username] = (token, timestamp)
            return chat_pb2.LoginReply(version=1,
                                    error_code="",
                                    auth_token=token,
                                    fullname=self.user_metadata_store[username][1])

    def CreateAccount(self, request, context) -> chat_pb2.AccountCreateReply:
        """
         Validates the request buffer and registers a new user with relevant metadata structures.

        Args:
            request (obj): Struct containing the user account information.

        Returns:
            chat_pb2.AccountCreateReply: Returns an `AccountCreateReply` 
            object that contains the version, error code,
            authentication token, and full name of the new user.
        """
        # get the given username and do basic error checking
        username = request.username
        
        with self.metadata_lock:
            if username in self.user_metadata_store.keys():
                return chat_pb2.AccountCreateReply(version=1, 
                                    error_code="ERROR Username Already Exists",
                                    auth_token="",
                                    fullname="")
            
            # get the password and do basic error checking
            password = request.password
            if self.ValidatePassword(password) < 0:
                return chat_pb2.AccountCreateReply(version=1, 
                                    error_code="ERROR Invalid Passcode",
                                    auth_token="",
                                    fullname="")
            
            # prepare metadata
            fullname = request.fullname
            token = self.GenerateToken()
            timestamp = self.utc_time_gen.now().timestamp()
            
            # create user metadata
            self.user_metadata_store[username] = (password, fullname)
            # register user in token hub / stores last given token
            self.token_hub[username] = (token, timestamp)
            
            with self.inbox_lock:
                # create user chat inbox
                self.user_inbox[username] = []
                return chat_pb2.AccountCreateReply(version=1,
                                                error_code="",
                                                auth_token=token,
                                                fullname=fullname)
        

    def ListAccounts(self, request, context) -> chat_pb2.ListAccountReply:
        """
        Validate the user's token, and return a list of usernames 
        filtered by a regular expression. 
        The list is limited to a maximum of 100 usernames.

        Args:
            request (obj)): The request struct containing the user request.

        Returns:
            chat_pb2.ListAccountReply: A socket type object containing the version, 
            error code and a comma-separated list of filtered usernames.
        """
        token = request.auth_token
        username = request.username
        if self.ValidateToken(username=username,
                              token=token) < 0:
            return chat_pb2.ListAccountReply(version=1,
                                             error_code="Invalid token",
                                             account_names="")
        with self.metadata_lock:
            list_of_usernames = self.user_metadata_store.keys()
        
        filtered_list = list_of_usernames
        # search using filter
        regex = request.regex
        if len(regex) != 0:
            r = re.compile(f".*{regex}")
            # filter based on compiled regex
            filtered_list = list(filter(r.match, list_of_usernames))
        filtered_string = ", ".join(filtered_list[:100])
        
        return chat_pb2.ListAccountReply(version=1,
                                         error_code="",
                                         account_names=filtered_string)
        
    def DeleteAccount(self, request, context) -> chat_pb2.DeleteAccountReply:
        """
        Deletes the user account and associated metadata, 
        including the user's inbox, based on a raw string buffer received from the user.

        Args:
            request (obj): The user request to validate and process.

        Returns:
            chat_pb2.DeleteAccountReply: A reply message that 
            indicates the success or failure of the operation. 
            The message contains a version number, an error code (if any), 
            and an empty string as a payload.
        """
        token = request.auth_token
        username = request.username
        if self.ValidateToken(username=username,
                              token=token) < 0:
            return chat_pb2.DeleteAccountReply(version=1,
                                             error_code="Invalid token")
            
        # delete all relevant metadata
        with self.metadata_lock:
            self.token_hub.pop(username)
            self.user_metadata_store.pop(username)
            with self.inbox_lock:
                self.user_inbox.pop(username)
                return chat_pb2.DeleteAccountReply(version=1,
                                                error_code="")
            
        
def serve():
    port = '50051'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServerServicer_to_server(ChatServer(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()