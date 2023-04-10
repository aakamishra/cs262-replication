import unittest
import json
from datetime import datetime, timedelta
from collections import defaultdict
from unittest.mock import MagicMock
from grpc_server import ChatServer

from colorama import Fore, Style

class TestChatServer(unittest.TestCase):
    def setUp(self):
        self.chat_server = ChatServer(1, "test")

    def test_get_state(self):
        expected_state = {
            "time": self.chat_server.utc_time_gen.utcnow().timestamp(),
            "user_inbox": defaultdict(list),
            "user_metadata_store": {},
            "token_hub": {},
            "commit_hash": hash(datetime.now())
        }
        result = json.loads(self.chat_server.get_state())

        del result["time"]
        del result["commit_hash"]
        del expected_state["time"]
        del expected_state["commit_hash"]

        self.assertDictEqual(result, expected_state)
        
    def test_get_state_time_created(self):
        # Test that the function returns the timestamp in the state correctly
        state = json.dumps({"time": self.chat_server.utc_time_gen.utcnow().timestamp()})
        self.assertEqual(self.chat_server.get_state_time_created(state), json.loads(state)["time"])
        
        # Test that the function returns 0 when there's an error loading the state
        state = "{'time': '1234'}" # invalid JSON
        self.assertEqual(self.chat_server.get_state_time_created(state), 0)
        
    def test_set_state(self):
        state = {
            "time": self.chat_server.utc_time_gen.utcnow().timestamp(),
            "user_inbox": defaultdict(list, {"user1": ["message1"]}),
            "user_metadata_store": {"user1": ["password1", "name1"]},
            "token_hub": {"user1": ["token1", self.chat_server.utc_time_gen.utcnow().timestamp()]},
            "commit_hash": hash(datetime.now())
        }
        self.chat_server.set_state(json.dumps(state))
        self.assertDictEqual(self.chat_server.user_inbox, state["user_inbox"])
        self.assertDictEqual(self.chat_server.user_metadata_store, state["user_metadata_store"])
        self.assertDictEqual(self.chat_server.token_hub, state["token_hub"])
        self.assertEqual(self.chat_server.state_save_time, state["time"])
        
        # Test that the function handles errors when loading the state
        self.chat_server.set_state("{'time': '1234'}") # invalid JSON
        self.assertEqual(self.chat_server.user_inbox, state["user_inbox"])
        self.assertEqual(self.chat_server.user_metadata_store, state["user_metadata_store"])
        self.assertEqual(self.chat_server.token_hub, state["token_hub"])
        self.assertEqual(self.chat_server.state_save_time, state["time"])

if __name__ == "__main__":
    test_obj = TestChatServer()
    test_obj.setUp()
    test_obj.test_get_state()
    test_obj.test_get_state_time_created()
    test_obj.test_set_state()
    print("Final Result:")
    print(Fore.GREEN + "Passed 3/3 Tests!")
