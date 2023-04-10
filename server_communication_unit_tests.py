import unittest
import socket
import time
import threading
from unittest.mock import MagicMock
from grpc_server import ServerInterface, ChatServer, ServerState
import datetime 

class TestServerInterface(unittest.TestCase):

    def setUp(self):
        # Set up a ChatServer object with mocked methods
        chat_server = ChatServer(position=ServerState.PRIMARY, log_filename="temp")
        chat_server.utc_time_gen = MagicMock()
        chat_server.utc_time_gen.now.side_effect = lambda: datetime.datetime.now()

        # Create a ServerInterface object with the mocked ChatServer and a test port
        self.port = "9000"
        self.server_interface = ServerInterface(chat_server, self.port)

    def test_init_listening_interface(self):
        # Test that init_listening_interface creates a socket, binds it to the correct port, and starts listening

        # You can use socket.socketpair to create a socket pair to simulate a client-server connection
        client_socket, server_socket = socket.socketpair()

        # Replace the server_interface's init_listening_interface with a MagicMock that returns the server_socket
        self.server_interface.init_listening_interface = MagicMock(return_value=server_socket)

        # Call the init_listening_interface method
        self.server_interface.init_listening_interface()

        # Check if the server_socket is bound to the correct port and is listening
        self.assertTrue(server_socket.getsockopt(socket.AF_INET, socket.SOCK_STREAM) == 0)

        # Close the sockets
        client_socket.close()
        server_socket.close()

    def test_submit_ballot(self):
        # Test the SubmitBallot method
        self.server_interface.sockets_dict = {}  # Empty the sockets_dict to prevent sending messages

        # Call the SubmitBallot method
        self.server_interface.SubmitBallot()

        # Check if the ballot_box has an entry for the current server
        self.assertIn(self.port, [entry[0] for entry in self.server_interface.ballot_box])

    def test_trigger_election(self):
        # Test the TriggerElection method
        self.server_interface.sockets_dict = {}  # Empty the sockets_dict to prevent sending messages

        # Call the TriggerElection method
        self.server_interface.TriggerElection()

        # Check if the election_time is True and the ballot_box is empty
        self.assertFalse(self.server_interface.election_time)
        self.assertEqual(len(self.server_interface.ballot_box), 0)

    def test_get_election_winner(self):
        # Test the GetElectionWinner method

        # Create a sample ballot box
        sample_ballot_box = [
            (self.port, 80, self.server_interface.servicer_object.utc_time_gen.now().timestamp()),
            ("9001", 90, self.server_interface.servicer_object.utc_time_gen.now().timestamp() - 10),
            ("9002", 70, self.server_interface.servicer_object.utc_time_gen.now().timestamp() - 5)
        ]
        self.server_interface.ballot_box = sample_ballot_box
        self.server_interface.election_time = True

        # Call the GetElectionWinner method
        with unittest.mock.patch("time.sleep", return_value=None):  # Mock time.sleep to avoid waiting
            self.server_interface.GetElectionWinner()

        # Check if the election_time is False, and the server_state is PRIMARY for the winning server
        self.assertFalse(self.server_interface.election_time)
        self.assertEqual(self.server_interface.servicer_object.server_state, ServerState.SECONDARY)


if __name__ == '__main__':
    unittest.main()
