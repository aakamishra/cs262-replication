import argparse
from enum import Enum
import chat_pb2_grpc
import chat_pb2
import binascii
import datetime
import time
import logging
import os
import re
import threading as th
import multiprocessing as mp
from collections import defaultdict
from concurrent import futures
import time 
import json
import grpc
from _thread import *
import socket
import wire_protocol as wp
import random

SECONDARY_ERROR_CODE = "Secondary server response"
INITIALIZE_WAIT_TIME = 10
REFRESH_TIME = 0.250
ELECTION_CHECK_TIME = 2 * REFRESH_TIME
ELECTION_ITERS = 100


EXTERNAL_SERVER_ADDRS = [("10.250.21.56", '50051'),
                         ('10.250.156.238', '50052'), ('10.250.156.238', '50053')]
INTERNAL_SERVER_ADDRS = [("10.250.21.56", '50054'),
                         ('10.250.156.238', '50055'), ('10.250.156.238', '50056')]

# EXTERNAL_SERVER_ADDRS = [("0.0.0.0", '50051'),
#                          ('0.0.0.0', '50052'), ('0.0.0.0', '50053')]
# INTERNAL_SERVER_ADDRS = [("0.0.0.0", '50054'),
#                          ('0.0.0.0', '50055'), ('0.0.0.0', '50056')]


class ServerState(Enum):
    PRIMARY = 1
    SECONDARY = 2
    BROKEN = 3
    ELECTION = 4


class ChatServer(chat_pb2_grpc.ChatServerServicer):
    def __init__(self, position, log_filename) -> None:
        super().__init__()
        self.user_inbox = defaultdict(lambda: [])

        # format of metadata store
        # key - username (must be unique)
        # per value entry (password, name)
        self.user_metadata_store = {}
        self.token_length = 15
        self.server_state = position

        # token hub keys are usernames and the values are token, timestamp
        # pairs
        self.token_hub = {}

        # keeping track of time by standardizing to UTC
        self.utc_time_gen = datetime.datetime

        # user metadata lock
        self.metadata_lock = th.Lock()

        # inbox lock
        self.inbox_lock = th.Lock()

        # where to store state in case of being primary
        self.state_file = f"logs/state_store_{log_filename}.txt"
        self.state_save_time = None

        self.commit_log_path = "logs/commit_log.txt"

        if os.path.exists(self.state_file):
            self.read_state_from_file()
    
    def get_state(self):
        # Returns state as a string that can be set by other servers
        with self.metadata_lock:
            with self.inbox_lock:
                self.state_save_time = time.time()
                self.prev_commit_hash = hash(self.state_save_time)
                return json.dumps(
                    {
                    "time": self.state_save_time,
                    "user_inbox": self.user_inbox,
                    "user_metadata_store": self.user_metadata_store, 
                    "token_hub": self.token_hub,
                    "commit_hash": self.prev_commit_hash
                    })

    def get_state_time_created(self, state):
        try:
            tm = json.loads(state)["time"]
        except:
            tm = 0 
            log_file = open(self.commit_log_path, "a")  # append mode
            log_file.write(f"Failing state: {state}\n")
            log_file.close()
        return tm
    
    def set_state(self, state):
        # Accepts string and sets state
        with self.metadata_lock:
            with self.inbox_lock:
                try:
                    state = json.loads(state)
                    self.user_inbox = state["user_inbox"]
                    self.user_metadata_store = state["user_metadata_store"]
                    self.token_hub = state["token_hub"]
                    self.state_save_time = state["time"]
                except:
                    log_file = open(self.commit_log_path, "a")  # append mode
                    log_file.write(f"Failing state: {state}\n")
                    log_file.close()
    
    def write_state(self):
        state = self.get_state()
        text_file = open(self.state_file, "w")
        text_file.write(state)
        text_file.close()
        
        log_file = open(self.commit_log_path, "a")  # append mode
        log_file.write(f"Commit Hash: {self.prev_commit_hash}, Time: {self.state_save_time} \n")
        log_file.close()
    
    def read_state_from_file(self):
        text_file = open(self.state_file, "r") # open text file in read mode
        state = text_file.read() # read whole file to a string
        text_file.close() # close file
        self.set_state(state)
    
    def update_state(self, state):
        with self.metadata_lock:
            with self.inbox_lock:
                cond = self.state_save_time is None or self.get_state_time_created(state) > self.state_save_time
        if cond:
            self.set_state(state)

    def ValidatePassword(self, password):
        """
        Validates a password to ensure that it is a string.

        Args:
            password (str): The password to validate.

        Returns:
            int: Returns 0 if the password is a string, or -1 if it is not.
        """
        if not isinstance(password, str):
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
        if self.server_state == ServerState.SECONDARY:
            return chat_pb2.MessageReply(
                version=1, error_code=SECONDARY_ERROR_CODE)
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
        self.write_state()
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
        token = request.auth_token
        username = request.username
        if self.server_state == ServerState.SECONDARY:
            return chat_pb2.RefreshReply(
                version=1, error_code=SECONDARY_ERROR_CODE)

        if self.ValidateToken(username=username,
                              token=token) < 0:
            return chat_pb2.RefreshReply(version=1,
                                         error_code="Invalid Token")
        # Check if there are any new messages
        while self.CheckInboxLength(username=username) > 0:
            with self.inbox_lock:
                msg = self.user_inbox[username].pop(0)
            # ended lock context before yield
            self.write_state()
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
        if self.server_state == ServerState.SECONDARY:
            return chat_pb2.LoginReply(
                error_code=SECONDARY_ERROR_CODE,
                auth_token="",
                fullname="")
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
        self.write_state()
        return chat_pb2.LoginReply(
            version=1,
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
        if self.server_state == ServerState.SECONDARY:
            return chat_pb2.AccountCreateReply(
                version=1,
                error_code=SECONDARY_ERROR_CODE,
                auth_token="",
                fullname="")
        with self.metadata_lock:
            if username in self.user_metadata_store.keys():
                return chat_pb2.AccountCreateReply(
                    version=1,
                    error_code="ERROR Username Already Exists",
                    auth_token="",
                    fullname="")

            # get the password and do basic error checking
            password = request.password
            if self.ValidatePassword(password) < 0:
                return chat_pb2.AccountCreateReply(
                    version=1, error_code="ERROR Invalid Passcode", auth_token="", fullname="")

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
        self.write_state()
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
        if self.server_state == ServerState.SECONDARY:
            return chat_pb2.ListAccountReply(version=1,
                                             error_code=SECONDARY_ERROR_CODE,
                                             account_names="")
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
            r = None
            try:
                r = re.compile(f".*{regex}")
            except Exception as e:
                return chat_pb2.ListAccountReply(version=1,
                                                 error_code=str(e),
                                                 account_names="")
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
        if self.server_state == ServerState.SECONDARY:
            return chat_pb2.DeleteAccountReply(version=1,
                                               error_code=SECONDARY_ERROR_CODE)
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
        self.write_state()
        return chat_pb2.DeleteAccountReply(version=1,
                                            error_code="")


class ServerInterface:
    """
    This class handles the inter-server communication logic.
    """

    def __init__(self, servicer_object: ChatServer, port: str):
        """
        Initialize the server interface with the servicer object and port number.
        """
        self.servicer_object = servicer_object
        self.port = port
        self.sockets_dict = {}
        self.replica_metadata = {}
        self.ballot_box = []
        self.iter_value = 0
        self.election_time = False

    def init_listening_interface(self) -> None:
        """
        Creates a new machine thread that monitors
        and accepts new client connections and hands
        them off to a newly created consumer thread.

        Args:
            None

        Returns:
            None
        """
        print(f"setting up listening interface for port {self.port}")
        # create the socket port for listening
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind to the port number
        s.bind(('0.0.0.0', int(self.port)))

        # start listening on port
        s.listen()

        for _ in range(2):
            conn, addr = s.accept()
            start_new_thread(self.consumer, (conn,))

    def consumer(self, conn) -> None:
        """
        Consumes data from a network connection and adds it to a queue.

        Args:
            conn (socket.socket): The network connection to consume data from.

        Returns:
            None

        """
        # Record the start time so we know when to stop consuming.
        while True:

            try:
                data = conn.recv(2048)
            except Exception as e:
                print("Connection Disrupted:", e, " - softhandler resolved")
                conn.close()
                return
            decoded = ""
            try:
                decoded = data.decode("UTF-8")
            except UnicodeDecodeError:
                print("Unable to decode the message")
                conn.close()

            args = decoded.split("||")
            if len(args) == 0:
                conn.close()
                return

            try:
                opcode = int(args[0])
            except ValueError:
                opcode = -1

            if opcode == 6:
                result = wp.socket_types.ServerStatusUpdate(data)
                if result is not None and result.port is not None:
                    self.replica_metadata[result.port] = (
                        result.position, self.servicer_object.utc_time_gen.now().timestamp())
                    if self.servicer_object.server_state == ServerState.PRIMARY and result.position == f"{ServerState.PRIMARY}":
                        print("Getting two primaries due to latency, triggering election!")
                        self.election_time = True
                        self.TriggerElection()
                        self.ballot_box = []
                        self.SubmitBallot()


            elif opcode == 7:
                result = wp.socket_types.ServerElectionTrigger(data)
                self.election_time = True
                self.ballot_box = []
                self.SubmitBallot()

            elif opcode == 8:
                result = wp.socket_types.ServerElectionBallot(data)
                if result is not None and result.port is not None:
                    self.ballot_box.append(
                        (result.port, result.value, self.servicer_object.utc_time_gen.now().timestamp()))
            
            elif opcode == 9:
                result = wp.socket_types.ServerSendState(data)
                # print(result.state)
                if result.state is not None:
                    self.servicer_object.update_state(result.state)
                else:
                    print(f"Sending None state: {result}")

    def inter_server_communication_thread(self):
        """
        This function starts a thread for inter-server communication.
        It listens for updates from other servers, initiates an election if necessary,
        and determines the winner of an election.
        """

        print("starting intercomms - checking internal state")
        print("Current Position State: ", self.servicer_object.server_state)

        print("Starting listening interface")
        # Start the thread for the listening interface
        init_thread = th.Thread(target=self.init_listening_interface)
        init_thread.start()

        # Add delay to initialize the server-side logic on all processes
        time.sleep(INITIALIZE_WAIT_TIME)

        # Connect to each server except for the current one
        for i in range(len(INTERNAL_SERVER_ADDRS)):
            host, port = INTERNAL_SERVER_ADDRS[i]
            if port != self.port:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sockets_dict[port] = s
                # self.replica_metadata[port] = (
                #     None, self.servicer_object.utc_time_gen.now().timestamp())

                try:
                    s.connect((host, int(port)))
                except Exception as e:
                    print(e)
        
        # time.sleep(2 * ELECTION_CHECK_TIME)

        if self.servicer_object.state_save_time is not None:
            state_msg = wp.encode.ServerSendState(version=1, state=self.servicer_object.get_state())
        else:
            state_msg = None
        
        for port in self.sockets_dict.keys():
            if state_msg is not None:
                try:
                    s = self.sockets_dict[port]
                    s.send(state_msg)
                except:
                    pass

        # Loop indefinitely
        while True:
            # Pause for a certain amount of time
            time.sleep(REFRESH_TIME)
            self.iter_value += 1

            # If an election is not in progress
            if not self.election_time:
                # Check if there is a primary server
                primary_found = False if self.servicer_object.server_state == ServerState.SECONDARY else True
                for port in self.sockets_dict.keys():
                    s = self.sockets_dict[port]
                    # Send an update on the current server's status to each
                    # connected server
                    msg = wp.encode.ServerStatusUpdate(
                        version=1, port=self.port, position=self.servicer_object.server_state)
                    if self.servicer_object.server_state == ServerState.PRIMARY:
                        state_msg = wp.encode.ServerSendState(version=1, state=self.servicer_object.get_state())
                    else:
                        state_msg = None
                    try:
                        s.send(msg)
                        if self.servicer_object.server_state == ServerState.PRIMARY:
                            s.send(state_msg)
                    except BrokenPipeError:
                        pass

                    # Check the metadata of each connected server to see if it
                    # has a primary server
                    if port in self.replica_metadata.keys():
                        pos, t = self.replica_metadata[port]
                        if self.servicer_object.utc_time_gen.now().timestamp() - t < ELECTION_CHECK_TIME:
                            if pos == f"{ServerState.PRIMARY}":
                                primary_found = True

                print(self.replica_metadata, " primary found: ", primary_found)

                # If no primary server is found after a certain number of
                # iterations, trigger an election
                if self.iter_value > ELECTION_ITERS and not primary_found:
                    print(f"Triggering Election: {self.port}")
                    self.election_time = True
                    self.TriggerElection()
                    time.sleep(2 * ELECTION_CHECK_TIME)
                    self.SubmitBallot()

            # If an election is in progress, determine the winner
            if self.election_time:
                self.GetElectionWinner()

    def SubmitBallot(self):
        """
        This function submits a ballot to each connected server during an election process.
        It generates a random election value and adds it to the ballot box along with the server's port and timestamp.
        It then sends a message to each connected server with the election value.
        """
        election_value = random.randint(1, 100)
        self.ballot_box.append(
            (self.port,
             election_value,
             self.servicer_object.utc_time_gen.now().timestamp()))
        for port in self.sockets_dict.keys():
            s = self.sockets_dict[port]
            msg = wp.encode.ServerElectionBallot(version=1,
                                                 port=self.port,
                                                 value=election_value)
            try:
                s.send(msg)
            except BrokenPipeError:
                pass

    def TriggerElection(self):
        """
        This function triggers an election process.
        It clears the ballot box and sends a message to each connected server indicating that an election has been triggered.
        """
        self.ballot_box = []
        for port in self.sockets_dict.keys():
            s = self.sockets_dict[port]
            msg = wp.encode.ServerElectionTrigger(version=1)
            try:
                s.send(msg)
            except BrokenPipeError:
                pass

    def GetElectionWinner(self):
        """
        This function waits for a certain amount of time after an election has been triggered and then determines the winner.
        It sorts the ballot box by election value and timestamp and selects the candidate with the highest value and most recent timestamp.
        If the current server is the winner, it updates its status to `ServerState.PRIMARY`.
        """
        time.sleep(8 * ELECTION_CHECK_TIME)
        # declare winner
        print("Ballot Box", self.ballot_box)
        primary_winner = sorted(
            self.ballot_box, key=lambda x: (x[1], -x[2]))[-1][0]
        print("Primary Winner: ", primary_winner)
        if self.port == primary_winner:
            self.servicer_object.server_state = ServerState.PRIMARY
            print(
                f"This Server is the new primary: {self.port}",
                "state: ",
                self.servicer_object.server_state)
        else:
            self.servicer_object.server_state = ServerState.SECONDARY
        # label any broken ports
        for port in self.replica_metadata.keys():
            if port != primary_winner and self.replica_metadata[
                    port][0] == f"{ServerState.PRIMARY}":
                self.replica_metadata[port] = (f"{ServerState.BROKEN}", self.servicer_object.utc_time_gen.now().timestamp())
        self.election_time = False


def serve(position, external_port, internal_port, log_file, timeout=None):
    """
    This function sets up a gRPC server and starts a thread for inter-server communication.
    The `position` parameter specifies the position of the server in the system (primary or secondary).
    The `external_port` parameter specifies the port number that external clients will use to connect to the server.
    The `internal_port` parameter specifies the port number that other instances of the server will use to communicate with this instance.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer_object = ChatServer(position=position, log_filename=log_file)
    chat_pb2_grpc.add_ChatServerServicer_to_server(servicer_object, server)
    server.add_insecure_port('[::]:' + external_port)
    interface = ServerInterface(
        servicer_object=servicer_object,
        port=internal_port)
    interface_thread = th.Thread(
        target=interface.inter_server_communication_thread)
    server.start()
    interface_thread.start()

    print("Server started, listening on " + internal_port)
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    parser = argparse.ArgumentParser(
        prog='gRPC-Python-Server',
        description='Spins a gRPC Chat server replica',
        epilog='Please see documentation for further help.')

    parser.add_argument(
        'position',
        default=ServerState.SECONDARY,
        help='primary-secondary position')
    parser.add_argument('external_port', default='5051', help='port value')
    parser.add_argument('internal_port', default='5054', help='port value')
    parser.add_argument('log_file', default='temp1', help='storage file name')

    parser.add_argument(
        '--timeout',
        default=None,
        help="option that determines the number of seconds till death")
    args = parser.parse_args()
    if args.position == 'p':
        position = ServerState.PRIMARY
    else:
        position = ServerState.SECONDARY

    print(args)
    serve(position, args.external_port, args.internal_port, args.log_file, args.timeout)
