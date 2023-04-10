# Chat Server Testing

## Running Unit Tests

For unit test of the 2-Fault and Persisent helper functionality run the following command:

```
python server_communication_unit_tests.py
```

For socket and gRPC unit tests, please run the following command:

```
python chat_server_unit_tests.py
```

For server state tests, run:
```
python server_state_tests.py
```

For client stub tests, run:
```
python client_stub_tests.py
```

## Description of 2-Fault / Persistent Unit Tests

`class TestServerInterface(unittest.TestCase):` A test class named TestServerInterface is defined, which inherits from unittest.TestCase. This allows the class to use the unittest framework for running test cases.

def setUp(self):: The setUp method is called before each test case. It sets up a mock ChatServer object and initializes a ServerInterface object with the mocked ChatServer and a test port. This is done to ensure that each test case starts with a clean and predictable state.

`def test_init_listening_interface(self):` This test case checks if the init_listening_interface method creates a socket, binds it to the correct port, and starts listening. It uses socket.socketpair() to create a pair of connected sockets to simulate a client-server connection, and replaces the init_listening_interface method with a MagicMock that returns the server-side socket. It then checks if the server-side socket is bound to the correct port and is listening.

`def test_submit_ballot(self):` This test case checks if the SubmitBallot method adds an entry for the current server in the ballot_box. It clears the sockets_dict to prevent sending messages and calls the SubmitBallot method. It then checks if the current server's port is in the ballot_box.

`def test_trigger_election(self):` This test case checks if the TriggerElection method sets election_time to False and clears the ballot_box. It clears the sockets_dict to prevent sending messages and calls the TriggerElection method. It then checks if election_time is False and the ballot_box is empty.

`def test_get_election_winner(self):` This test case checks if the GetElectionWinner method sets election_time to False and updates the server_state for the winning server. It creates a sample ballot_box and sets election_time to True. The time.sleep function is mocked to avoid waiting during the test execution. It then calls the GetElectionWinner method and checks if election_time is False, and the server_state is PRIMARY for the winning server.

## Description of Chat Server Unit Tests

The first function, `GenerateTokenTest()`, tests the token generation functionality of both chat servers by generating two tokens from each server and asserting that the two generated tokens are not the same.

The second function, `CreateAccountTest()`, tests the account creation functionality of both chat servers. It instantiates a server, defines an account creation message, calls the account creation method of the server with the message and context, asserts that there were no errors returned by the server, and checks if the newly created account is stored in the server's user metadata store. It also asserts that calling the account creation method again with the same message and context results in an error being returned by the server.

The third function, `ValidateTokenTest()`, tests the token verification capability of both chat servers. It instantiates a server, creates a request object to create a new user account, sends the account creation request to the server and gets the response, extracts the user's auth token and username from the response, validates the token and username on the server, and asserts that the response is valid.

In the `LoginTest` function, the code first creates a user account and then tests the login functionality by passing correct and incorrect passwords to the server. It then tests the socket implementation of the login functionality using the same approach.

In the `SendMessageTest` function, the code creates two user accounts, and then sends a message from one user to another using both the gRPC and socket implementation of the server. The code then verifies that the message was successfully delivered to the recipient.

We then create a test suite for testing the `ListAccounts` and `DeleteAccount` functionality for the chat servers.

The `ListAccounts` function is called twice: first using an instance of `gRPCChatServer`, and then using an instance of `SocketChatServer`. In each instance, several accounts are created and then the accounts are listed using two different regular expressions for account names. The test suite checks if the accounts are listed correctly and if an error code is returned when an invalid regular expression is used.

The `DeleteAccount` function creates four accounts using `gRPCChatServer` and deletes the first account created. It checks if the account was deleted correctly and if an error code is returned when an invalid account is specified for deletion.

## Description of Client Side Tests

Our client side tests tested especially the new functionality on the client-side
(which wasn't much) to reach out to multiple servers and aggregate multiple
responses and only use the one from the primary.

Test 1 (test_try_except_RPC_error):
This test verifies that the try_except_RPC_error function properly catches and handles any grpc.RpcError exceptions thrown by a mocked function. The test creates a mocked function that always raises an grpc.RpcError exception when called. The try_except_RPC_error function is then used to wrap the mocked function, and the wrapped function is called. The test verifies that the wrapped function returns None, as expected.

Test 2 (test_SendRequest_with_RPC_error):
This test verifies that the SendRequest function properly handles a grpc.RpcError exception thrown by one of the gRPC server stubs. The test creates a mocked gRPC server stub that always raises a grpc.RpcError exception when the CreateAccount method is called. The mocked server stub is then used to create a ClientStub instance, which is configured to use only the mocked server stub. The SendRequest method is then called on the ClientStub instance with the CreateAccount method and a dictionary of parameters. The test verifies that an Exception is raised, with the expected error message.

Test 3 (test_SendRequest_with_One_Primary_Multiple_Secondaries):
This test verifies that the SendRequest function properly handles a scenario where there is one primary gRPC server and multiple secondary servers. The test creates three mocked server stubs, where the first two stubs always return a MockReply object with the error code SECONDARY_ERROR_CODE when the CreateAccount method is called, and the third stub returns a MockReply object with the error code "" and a val attribute set to 100. A ClientStub instance is then created with these mocked server stubs, and the SendRequest method is called on the ClientStub instance with the CreateAccount method and a dictionary of parameters. The test verifies that the val attribute of the returned MockReply object is equal to 100, as expected.

Test 4 (test_SendRequest_with_Multiple_Primaries):
This test verifies that the SendRequest function properly handles a scenario where there are multiple primary gRPC servers (erroneous). The test creates two mocked server stubs, where both stubs always return a MockReply object with the error code "" when the CreateAccount method is called. A ClientStub instance is then created with these mocked server stubs, and the SendRequest method is called on the ClientStub instance with the CreateAccount method and a dictionary of parameters. The test verifies that an Exception is raised, with the expected error message of seeing multiple primaries.

## Description of Server State Tests

We wrote some simple unit tests to verify that the state was being set and gotten correctly for the state syncing procedure. See `server_state_tests.py` for these
tests.

## (Bonus) Running Integration Tests

For grpc integration tests, please run the following command:

```
python grpc_integration_tests.py
```

## Description of Integration Tests

Our code test tests concurrency, specifically concurrent message sending and receiving, for a client application. It does this by running a set of integration tests using a ClientApplication object that is created with the given username, password, fullname, and account_status parameters.

The integration tests check whether the application is able to create an account and login successfully, list the created account, send a message to another client application, and concurrently listen for incoming messages from other clients.

To simulate concurrent message sending and receiving, the code creates two threads: one to listen for messages using the Listen function, and another to send messages using the SendMessage function. The Listen function runs in an infinite loop and waits for messages from other clients. The SendMessage function sends a message to another client and waits for a response.

The code tests for concurrency by pausing the main thread for 2 seconds after sending a message, and then checking for the incoming message in the Listen function. If the message is received, it is printed as a success message. Otherwise, an error message is printed with the expected and actual values. We do this with 4 threads at the same time. 

We also test on the effect of deleting an node from the loop of messages being sent and the ability for the server to handle lists, requests and messages sent to and from the processes without process "c". This test ensures that our locking and access system is consistent.

If the integration tests pass successfully, the function returns an integer value of 0. If any of the tests fail, the function raises an assertion error, which stops the program.