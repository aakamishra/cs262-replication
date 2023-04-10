from colorama import Fore, Style

import chat_pb2
import wire_protocol as wp
from grpc_server import ChatServer as gRPCChatServer
from socket_server import ChatServer as SocketChatServer


def GenerateTokenTest():
    """
    Define a function to test token generation functionality
    of gRPC and socket chat servers.
    """

    # Instantiate a gRPC chat server
    server = gRPCChatServer()

    # Generate two tokens from the gRPC chat server
    token1 = server.GenerateToken()
    token2 = server.GenerateToken()

    # Assert that the two generated tokens are not the same
    assert token1 != token2
    print(Fore.GREEN + "gRPC GenerateTokenTest Passed" + Style.RESET_ALL)

    # Instantiate a socket chat server
    server = SocketChatServer()

    # Generate two tokens from the socket chat server
    token1 = server.GenerateToken()
    token2 = server.GenerateToken()

    # Assert that the two generated tokens are not the same
    assert token1 != token2
    print(Fore.GREEN + "Socket GenerateTokenTest Passed" + Style.RESET_ALL)


def CreateAccountTest():
    """
    Define a function to test the account creation
    functionality of gRPC and socket chat servers.
    """

    # Instantiate a gRPC chat server
    server = gRPCChatServer()

    # Define an account creation message
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="aakamishra",
                                        password="hahaha",
                                        fullname="Aakash Mishra")

    # Define a context for the gRPC method call
    context = {}

    # Call the account creation method of the gRPC chat server with the
    # message and context
    resp = server.CreateAccount(msg, context)

    # Assert that there were no errors returned by the server
    assert len(resp.error_code) == 0

    # Assert that the newly created account is stored in the server's user
    # metadata store
    assert "aakamishra" in server.user_metadata_store.keys()

    # Call the account creation method again with the same message and context
    resp = server.CreateAccount(msg, context)

    # Assert that an error was returned by the server this time
    assert len(resp.error_code) > 0
    print(Fore.GREEN + "gRPC CreateAccountTest Passed" + Style.RESET_ALL)

    # Instantiate a socket chat server
    server = SocketChatServer()

    # Define an account creation message
    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="aakamishra",
                                         password="hahaha",
                                         fullname="Aakash Mishra")

    # Call the account creation method of the socket chat server with the
    # message
    raw = server.CreateAccount(msg)
    resp = wp.socket_types.AccountCreateReply(raw)

    # Assert that there were no errors returned by the server
    assert len(resp.error_code) == 0

    # Assert that the newly created account is stored in the server's user
    # metadata store
    assert "aakamishra" in server.user_metadata_store.keys()

    # Call the account creation method again with the same message
    raw = server.CreateAccount(msg)
    resp = wp.socket_types.AccountCreateReply(raw)

    # Assert that an error was returned by the server this time
    assert len(resp.error_code) > 0

    # Call the account creation method with an invalid buffer
    raw = server.CreateAccount("invalid-buffer".encode("ascii"))
    resp = wp.socket_types.AccountCreateReply(raw)

    # Assert that an error was returned by the server
    assert len(resp.error_code) > 0
    print(Fore.GREEN + "Socket CreateAccountTest Passed" + Style.RESET_ALL)


def ValidateTokenTest():
    """
    Test chat server capability for token verification.
    """
    # Instantiate a gRPC chat server object
    server = gRPCChatServer()
    # Create a request object to create a new user account
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="aakamishra",
                                        password="hahaha",
                                        fullname="Aakash Mishra")
    context = {}
    # Send the account creation request to the server and get the response
    resp = server.CreateAccount(msg, context)
    # Extract the user's auth token and username from the response
    token = resp.auth_token
    username = msg.username
    # Validate the token and username on the server
    resp = server.ValidateToken(username=username, token=token)
    # Check that the response is valid (in this case, 0 means success)
    assert resp == 0
    print(Fore.GREEN + "gRPC ValidateTokenTest Passed" + Style.RESET_ALL)

    # Instantiate a Socket chat server object
    server = SocketChatServer()
    # Create a request object to create a new user account
    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="aakamishra",
                                         password="hahaha",
                                         fullname="Aakash Mishra")
    # Send the account creation request to the server and get the response
    raw = server.CreateAccount(msg)
    resp = wp.socket_types.AccountCreateReply(raw)
    # Extract the user's auth token and username from the response
    token = resp.auth_token
    username = "aakamishra"
    # Validate the token and username on the server
    resp = server.ValidateToken(username=username, token=token)
    # Check that the response is valid (in this case, 0 means success)
    assert resp == 0
    print(Fore.GREEN + "Socket ValidateTokenTest Passed" + Style.RESET_ALL)


def LoginTest():
    """
    Test the gRPC and socket implementation of the Login function.
    """
    # Create an instance of the gRPC Chat Server
    server = gRPCChatServer()

    # Create an account for the user
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="aakamishra",
                                        password="hahaha",
                                        fullname="Aakash Mishra")
    context = {}
    resp = server.CreateAccount(msg, context)

    # Test the Login function with correct username and password
    msg = chat_pb2.LoginRequest(version=1,
                                username="aakamishra",
                                password="hahaha")
    resp = server.Login(msg, context)
    assert len(resp.error_code) == 0  # check if the error code is empty
    assert len(resp.auth_token) > 0    # check if the auth token is present

    # Test the Login function with incorrect password
    msg = chat_pb2.LoginRequest(version=1,
                                username="aakamishra",
                                password="hah")
    resp = server.Login(msg, context)
    assert len(resp.error_code) > 0    # check if the error code is non-empty
    assert len(resp.auth_token) == 0   # check if the auth token is not present
    print(Fore.GREEN + "gRPC LoginTest Passed" + Style.RESET_ALL)

    # Test the Socket implementation of the Login function
    server = SocketChatServer()

    # Create an account for the user
    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="aakamishra",
                                         password="hahaha",
                                         fullname="Aakash Mishra")
    raw = server.CreateAccount(msg)
    resp = wp.socket_types.AccountCreateReply(raw)

    # Test the Login function with correct username and password
    msg = wp.encode.LoginRequest(version=1,
                                 username="aakamishra",
                                 password="hahaha")
    raw = server.Login(msg)
    resp = wp.socket_types.LoginReply(raw)
    assert len(resp.error_code) == 0  # check if the error code is empty
    assert len(resp.auth_token) > 0    # check if the auth token is present

    # Test the Login function with incorrect password
    msg = wp.encode.LoginRequest(version=1,
                                 username="aakamishra",
                                 password="haha")
    raw = server.Login(msg)
    resp = wp.socket_types.LoginReply(raw)

    assert len(resp.error_code) > 0    # check if the error code is non-empty
    assert len(resp.auth_token) == 0   # check if the auth token is not present

    # Test the Login function with an invalid buffer
    raw = server.Login("invalid-buffer".encode("ascii"))
    resp = wp.socket_types.LoginReply(raw)
    assert len(resp.error_code) > 0    # check if the error code is non-empty
    print(Fore.GREEN + "Socket LoginTest Passed" + Style.RESET_ALL)


def SendMessageTest():
    """
    This function is used to test the message sending functionality.
    """

    # Instantiate a gRPCChatServer object
    server = gRPCChatServer()

    # Create a new account using the gRPCChatServer object and get the auth
    # token of the user
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="aakamishra",
                                        password="hahaha",
                                        fullname="Aakash Mishra")
    context = {}
    original_resp = server.CreateAccount(msg, context)

    # Create another account using the gRPCChatServer object
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="apumishra",
                                        password="hahaha",
                                        fullname="Apurva Mishra")
    context = {}
    resp = server.CreateAccount(msg, context)

    # Send a message from the first user to the second user using the
    # gRPCChatServer object
    msg = chat_pb2.MessageRequest(version=1,
                                  username="aakamishra",
                                  auth_token=original_resp.auth_token,
                                  recipient_username="apumishra",
                                  message="hi!")
    resp = server.SendMessage(msg, context)

    # Verify that there are no errors in the message sending process and that
    # the message was received by the recipient
    assert len(resp.error_code) == 0
    assert len(server.user_inbox["apumishra"]) > 0
    print(Fore.GREEN + "gRPC SendMessageTest Passed" + Style.RESET_ALL)

    # Instantiate a SocketChatServer object
    server = SocketChatServer()

    # Create a new account using the SocketChatServer object and get the auth
    # token of the user
    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="aakamishra",
                                         password="hahaha",
                                         fullname="Aakash Mishra")
    raw = server.CreateAccount(msg)
    original_resp = wp.socket_types.AccountCreateReply(raw)

    # Create another account using the SocketChatServer object
    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="apumishra",
                                         password="hahaha",
                                         fullname="Apurva Mishra")
    raw = server.CreateAccount(msg)
    resp = wp.socket_types.AccountCreateReply(raw)

    # Send a message from the first user to the second user using the
    # SocketChatServer object
    msg = wp.encode.MessageRequest(version=1,
                                   username="aakamishra",
                                   auth_token=original_resp.auth_token,
                                   recipient_username="apumishra",
                                   message="hi!")
    raw = server.ReceiveMessage(msg)
    resp = wp.socket_types.MessageReply(raw)

    # Verify that there are no errors in the message sending process and that
    # the message was received by the recipient
    assert len(resp.error_code) == 0
    assert len(server.user_inbox["apumishra"]) > 0

    # Test the error handling of the SocketChatServer object by sending an
    # invalid buffer to the server
    raw = server.ReceiveMessage("invalid-buffer".encode("ascii"))
    resp = wp.socket_types.MessageReply(raw)
    assert len(resp.error_code) > 0
    print(Fore.GREEN + "Socket SendMessageTest Passed" + Style.RESET_ALL)


def DeliverMessageTest():
    """
    Test chat server message delivery.
    """

    # Create a gRPCChatServer object
    server = gRPCChatServer()

    # Create two AccountCreateRequest messages, one for each user, and send
    # them to the server to create the accounts
    msg = chat_pb2.AccountCreateRequest(
        version=1,
        username="aakamishra",
        password="hahaha",
        fullname="Aakash Mishra")
    context = {}
    original_resp = server.CreateAccount(msg, context)

    msg = chat_pb2.AccountCreateRequest(
        version=1,
        username="apumishra",
        password="hahaha",
        fullname="Apurva Mishra")
    context = {}
    second_resp = server.CreateAccount(msg, context)

    # Create a MessageRequest message from aakamishra to apumishra, and send
    # it to the server to deliver the message
    msg = chat_pb2.MessageRequest(
        version=1,
        username="aakamishra",
        auth_token=original_resp.auth_token,
        recipient_username="apumishra",
        message="hi!")
    resp = server.SendMessage(msg, context)

    # Create a RefreshRequest message from apumishra, and send it to the
    # server to deliver any messages in their inbox
    msg = chat_pb2.RefreshRequest(
        version=1,
        auth_token=second_resp.auth_token,
        username="apumishra")

    # Loop through the messages returned by the DeliverMessages method, and
    # assert that the first message matches the expected message
    for m in server.DeliverMessages(msg, context):
        assert m.message == "[aakamishra]: hi!"
        break
    print(Fore.GREEN + "gRPC DeliverMessageTest Passed" + Style.RESET_ALL)

    # Create a SocketChatServer object
    server = SocketChatServer()

    # Create two AccountCreateRequest messages, one for each user, and send
    # them to the server to create the accounts
    msg = wp.encode.AccountCreateRequest(
        version=1,
        username="aakamishra",
        password="hahaha",
        fullname="Aakash Mishra")
    raw = server.CreateAccount(msg)
    original_resp = wp.socket_types.AccountCreateReply(raw)

    msg = wp.encode.AccountCreateRequest(
        version=1,
        username="apumishra",
        password="hahaha",
        fullname="Apurva Mishra")
    raw = server.CreateAccount(msg)
    second_resp = wp.socket_types.AccountCreateReply(raw)

    # Create a MessageRequest message from aakamishra to apumishra, and send
    # it to the server to deliver the message
    msg = wp.encode.MessageRequest(
        version=1,
        username="aakamishra",
        auth_token=original_resp.auth_token,
        recipient_username="apumishra",
        message="hi!")
    raw = server.ReceiveMessage(msg)
    resp = wp.socket_types.MessageReply(raw)

    # Create a RefreshRequest message from apumishra, and send it to the
    # server to deliver any messages in their inbox
    msg = wp.encode.RefreshRequest(
        version=1,
        auth_token=second_resp.auth_token,
        username="apumishra")

    # Call the DeliverMessages method and assert that the returned message
    # matches the expected message
    raw = server.DeliverMessages(msg)
    resp = wp.socket_types.RefreshReply(raw)
    assert resp.message == "[aakamishra]: hi!"

    # Call the DeliverMessages method with an invalid buffer, and assert that
    # the returned error code is greater than zero
    raw = server.DeliverMessages("invalid-buffer".encode("ascii"))
    resp = wp.socket_types.RefreshReply(raw)
    assert len(resp.error_code) > 0
    print(Fore.GREEN + "Socket DeliverMessageTest Passed" + Style.RESET_ALL)


def ListAccountsTest():
    """
    Test List accounts functionality for the chat server.
    """

    # initialize a gRPCChatServer
    server = gRPCChatServer()

    # create an account with the given username, password, and full name
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="aakamishra",
                                        password="hahaha",
                                        fullname="Aakash Mishra")

    # set context to an empty dictionary
    context = {}

    # create an account using the server and msg
    original_resp = server.CreateAccount(msg, context)

    # create three more accounts using similar code above
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="apumishra",
                                        password="hahaha",
                                        fullname="Apurva Mishra")
    context = {}
    second_resp = server.CreateAccount(msg, context)

    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="rajatmittal",
                                        password="lol",
                                        fullname="Rajat Mittal")
    context = {}
    second_resp = server.CreateAccount(msg, context)

    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="jwaldo",
                                        password="lol",
                                        fullname="Jim Waldo")
    context = {}
    second_resp = server.CreateAccount(msg, context)

    # list all the accounts with the given auth token
    msg = chat_pb2.ListAccountRequest(version=1,
                                      username="aakamishra",
                                      auth_token=original_resp.auth_token,
                                      regex=".*")
    resp = server.ListAccounts(msg, context)

    # check if the listed account names match the expected output
    assert resp.account_names == "aakamishra, apumishra, rajatmittal, jwaldo"

    # list accounts again, but with a different regex parameter
    msg = chat_pb2.ListAccountRequest(version=1,
                                      username="aakamishra",
                                      auth_token=original_resp.auth_token,
                                      regex="*.")
    resp = server.ListAccounts(msg, context)

    # check if an error code was returned for the second list request
    assert len(resp.error_code) > 0
    print(Fore.GREEN + "gRPC ListAccountsTest Passed" + Style.RESET_ALL)

    # switch to using the SocketChatServer
    server = SocketChatServer()

    # create four accounts using similar code above
    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="aakamishra",
                                         password="hahaha",
                                         fullname="Aakash Mishra")
    raw = server.CreateAccount(msg)
    original_resp = wp.socket_types.AccountCreateReply(raw)

    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="apumishra",
                                         password="hahaha",
                                         fullname="Apurva Mishra")
    raw = server.CreateAccount(msg)
    second_resp = wp.socket_types.AccountCreateReply(raw)

    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="rajatmittal",
                                         password="lol",
                                         fullname="Rajat Mittal")
    raw = server.CreateAccount(msg)
    resp = wp.socket_types.AccountCreateReply(raw)

    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="jwaldo",
                                         password="lol",
                                         fullname="Jim Waldo")
    raw = server.CreateAccount(msg)
    resp = wp.socket_types.AccountCreateReply(raw)

    msg = wp.encode.ListAccountRequest(version=1,
                                       auth_token=original_resp.auth_token,
                                       username="aakamishra",
                                       regex=".*",
                                       number_of_accounts=10)

    raw = server.ListAccounts(msg)
    resp = wp.socket_types.ListAccountReply(raw)

    assert resp.account_names == "aakamishra, apumishra, rajatmittal, jwaldo"

    msg = wp.encode.ListAccountRequest(version=1,
                                       auth_token=original_resp.auth_token,
                                       username="aakamishra",
                                       regex="*.",
                                       number_of_accounts=10)

    # check if an error code was returned for the second list request
    raw = server.ListAccounts(msg)
    resp = wp.socket_types.ListAccountReply(raw)
    assert len(resp.error_code) > 0

    # check if an error code was returned for the invalid buffer
    raw = server.ListAccounts("invalid-buffer".encode("ascii"))
    resp = wp.socket_types.ListAccountReply(raw)
    assert len(resp.error_code) > 0
    print(Fore.GREEN + "Socket ListAccountsTest Passed" + Style.RESET_ALL)


def DeleteAccountTest():
    """
    Define a function for testing delete account functionality.
    """
    # Create an instance of the gRPCChatServer
    server = gRPCChatServer()

    # Create a new account named 'aakamishra'
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="aakamishra",
                                        password="hahaha",
                                        fullname="Aakash Mishra")
    context = {}
    original_resp = server.CreateAccount(msg, context)

    # Create a new account named 'apumishra'
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="apumishra",
                                        password="hahaha",
                                        fullname="Apurva Mishra")
    context = {}
    second_resp = server.CreateAccount(msg, context)

    # Create a new account named 'rajatmittal'
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="rajatmittal",
                                        password="lol",
                                        fullname="Rajat Mittal")
    context = {}
    third_resp = server.CreateAccount(msg, context)

    # Create a new account named 'jwaldo'
    msg = chat_pb2.AccountCreateRequest(version=1,
                                        username="jwaldo",
                                        password="lol",
                                        fullname="Jim Waldo")
    context = {}
    fourth_resp = server.CreateAccount(msg, context)

    # Delete the 'rajatmittal' account
    msg = chat_pb2.DeleteAccountRequest(version=1,
                                        auth_token=third_resp.auth_token,
                                        username="rajatmittal")
    resp = server.DeleteAccount(msg, context)

    # Check that there are no errors with the deletion
    assert len(resp.error_code) == 0

    # Try to delete the 'rajatmittal' account again
    resp = server.DeleteAccount(msg, context)

    # Check that there is an error with the deletion
    assert len(resp.error_code) > 0

    # List all the existing accounts except 'rajatmittal'
    msg = chat_pb2.ListAccountRequest(version=1,
                                      username="aakamishra",
                                      auth_token=original_resp.auth_token,
                                      regex=".*")
    resp = server.ListAccounts(msg, context)

    # Check that the existing accounts are 'aakamishra', 'apumishra' and
    # 'jwaldo'
    assert resp.account_names == "aakamishra, apumishra, jwaldo"

    # Print message indicating that the gRPC DeleteAccountTest passed
    print(Fore.GREEN + "gRPC DeleteAccountTest Passed" + Style.RESET_ALL)

    # Create an instance of the SocketChatServer
    server = SocketChatServer()

    # Create a new account named 'aakamishra'
    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="aakamishra",
                                         password="hahaha",
                                         fullname="Aakash Mishra")
    raw = server.CreateAccount(msg)
    original_resp = wp.socket_types.AccountCreateReply(raw)

    # Create a new account named 'apumishra'
    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="apumishra",
                                         password="hahaha",
                                         fullname="Apurva Mishra")
    raw = server.CreateAccount(msg)
    second_resp = wp.socket_types.AccountCreateReply(raw)

    # Create a new account named 'rajatmittal'
    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="rajatmittal",
                                         password="lol",
                                         fullname="Rajat Mittal")

    raw = server.CreateAccount(msg)
    third_resp = wp.socket_types.AccountCreateReply(raw)

    msg = wp.encode.AccountCreateRequest(version=1,
                                         username="jwaldo",
                                         password="lol",
                                         fullname="Jim Waldo")
    raw = server.CreateAccount(msg)
    fourth_resp = wp.socket_types.AccountCreateReply(raw)

    msg = wp.encode.DeleteAccountRequest(version=1,
                                         auth_token=third_resp.auth_token,
                                         username="rajatmittal")

    # Delete one of the accounts using a valid auth token
    raw = server.DeleteAccount(msg)
    resp = wp.socket_types.DeleteAccountReply(raw)

    assert len(resp.error_code) == 0

    # test invalid repeated delete
    raw = server.DeleteAccount(msg)
    resp = wp.socket_types.DeleteAccountReply(raw)

    assert len(resp.error_code) > 0

    # list accounts to make sure the deleted account does not appear
    msg = wp.encode.ListAccountRequest(version=1,
                                       auth_token=original_resp.auth_token,
                                       username="aakamishra",
                                       regex=".*",
                                       number_of_accounts=10)

    raw = server.ListAccounts(msg)
    resp = wp.socket_types.ListAccountReply(raw)

    # assert groud truth existing users
    assert resp.account_names == "aakamishra, apumishra, jwaldo"

    # check invalid buffer input
    raw = server.DeleteAccount("invalid-buffer".encode("ascii"))
    resp = wp.socket_types.DeleteAccountReply(raw)
    assert len(resp.error_code) > 0

    print(Fore.GREEN + "Socket DeleteAccountTest Passed" + Style.RESET_ALL)


if __name__ == "__main__":
    print("Begin Unit Tests for Sockets and gRPC")
    GenerateTokenTest()
    CreateAccountTest()
    ValidateTokenTest()
    LoginTest()
    SendMessageTest()
    DeliverMessageTest()
    ListAccountsTest()
    DeleteAccountTest()
    print("Final Result:")
    print(Fore.GREEN + "Passed 42/42 Tests!")
