import unittest
from unittest.mock import MagicMock
from client import ClientStub, try_except_RPC_error, SECONDARY_ERROR_CODE

from colorama import Fore, Style

import grpc

class MockReply:
    def __init__(self, error_code):
        self.error_code = error_code

class TestClientStub(unittest.TestCase):

    def test_try_except_RPC_error(self):
        # Mock function that raises grpc.RpcError
        mock_func = MagicMock(side_effect=grpc.RpcError())

        # Wrap function with try_except_RPC_error
        wrapped_func = try_except_RPC_error(mock_func)

        # Call wrapped function
        result = wrapped_func()

        # Verify that wrapped function returns None
        self.assertIsNone(result)

    def test_SendRequest_with_RPC_error(self):
        # Mock ChatServerStub
        mock_stub = MagicMock()
        mock_stub.CreateAccount.side_effect = grpc.RpcError()

        # Create ClientStub with mock ChatServerStub
        client_stub = ClientStub(['localhost'], [50051])

        # Replace self.stubs with mock_stub
        client_stub.stubs = [mock_stub]

        # Call SendRequest
        with self.assertRaises(Exception) as context:
            result = client_stub.SendRequest('CreateAccount', {'username': 'test_user', 'password': 'test_password', 'fullname': 'Test User'})

        self.assertEqual(str(context.exception), "No servers believe they are the primary!")

    def test_SendRequest_with_One_Primary_Multiple_Secondaries(self):
        # Mock ChatServerStub
        mock_stub_1 = MagicMock()
        mock_stub_1.CreateAccount.return_value = MockReply(error_code=SECONDARY_ERROR_CODE)

        mock_stub_2 = MagicMock()
        mock_stub_2.CreateAccount.return_value = MockReply(error_code=SECONDARY_ERROR_CODE)

        mock_stub_3 = MagicMock()
        mock_reply = MockReply(error_code="")
        mock_reply.val = 100
        mock_stub_3.CreateAccount.return_value = mock_reply
        

        # Create ClientStub with mock ChatServerStub
        client_stub = ClientStub(['localhost', 'localhost', 'localhost'], [50051, 50052, 50053])

        # Replace self.stubs with mock_stub
        client_stub.stubs = [mock_stub_1, mock_stub_2, mock_stub_3]

        # Call SendRequest
        result = client_stub.SendRequest('CreateAccount', {'username': 'test_user', 'password': 'test_password', 'fullname': 'Test User'})

        self.assertEqual(result.val, 100)

    def test_SendRequest_with_Multiple_Primaries(self):
        # Mock ChatServerStub
        mock_stub_1 = MagicMock()
        mock_stub_1.CreateAccount.return_value = MockReply(error_code="")

        mock_stub_2 = MagicMock()
        mock_stub_2.CreateAccount.return_value = MockReply(error_code="")

        # Create ClientStub with mock ChatServerStub
        client_stub = ClientStub(['localhost', 'localhost'], [50051, 50052])

        # Replace self.stubs with mock_stub
        client_stub.stubs = [mock_stub_1, mock_stub_2]

        # Call SendRequest
        with self.assertRaises(Exception) as context:
            result = client_stub.SendRequest('CreateAccount', {'username': 'test_user', 'password': 'test_password', 'fullname': 'Test User'})

        self.assertEqual(str(context.exception), "Two servers believe they are the primary!")

if __name__ == "__main__":
    print("Beginning Unit Tests for Client gRPC Stubs")
    test_obj = TestClientStub()
    test_obj.test_try_except_RPC_error()
    test_obj.test_SendRequest_with_RPC_error()
    test_obj.test_SendRequest_with_One_Primary_Multiple_Secondaries()
    test_obj.test_SendRequest_with_Multiple_Primaries()
    print("Final Result:")
    print(Fore.GREEN + "Passed 4/4 Tests!")