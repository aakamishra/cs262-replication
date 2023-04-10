# Chat Server Testing

## Running Unit Tests

For socket and gRPC unit tests, please run the following command:

```
python unit_tests.py
```

## Description of Chat Server Unit Tests

The first function, `GenerateTokenTest()`, tests the token generation functionality of both chat servers by generating two tokens from each server and asserting that the two generated tokens are not the same.

The second function, `CreateAccountTest()`, tests the account creation functionality of both chat servers. It instantiates a server, defines an account creation message, calls the account creation method of the server with the message and context, asserts that there were no errors returned by the server, and checks if the newly created account is stored in the server's user metadata store. It also asserts that calling the account creation method again with the same message and context results in an error being returned by the server.

The third function, `ValidateTokenTest()`, tests the token verification capability of both chat servers. It instantiates a server, creates a request object to create a new user account, sends the account creation request to the server and gets the response, extracts the user's auth token and username from the response, validates the token and username on the server, and asserts that the response is valid.

In the `LoginTest` function, the code first creates a user account and then tests the login functionality by passing correct and incorrect passwords to the server. It then tests the socket implementation of the login functionality using the same approach.

In the `SendMessageTest` function, the code creates two user accounts, and then sends a message from one user to another using both the gRPC and socket implementation of the server. The code then verifies that the message was successfully delivered to the recipient.

We then create a test suite for testing the `ListAccounts` and `DeleteAccount` functionality for the chat servers.

The `ListAccounts` function is called twice: first using an instance of `gRPCChatServer`, and then using an instance of `SocketChatServer`. In each instance, several accounts are created and then the accounts are listed using two different regular expressions for account names. The test suite checks if the accounts are listed correctly and if an error code is returned when an invalid regular expression is used.

The `DeleteAccount` function creates four accounts using `gRPCChatServer` and deletes the first account created. It checks if the account was deleted correctly and if an error code is returned when an invalid account is specified for deletion.

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