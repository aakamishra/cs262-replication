# Current Project Entries





# Previous Project Entries


## Entry 2/9/2023 11:00 am

Worked on looking at documentation of the the python GrPC protocol online and worked through the demo example provided regarding latitude and longitude coordinate transfer. 
Talked about how we do not have to stream things messages, because each message can be treated as its own operation rather than a streaming operation.

We then used the HelloWorld proto base template to get started with our application. We notice that routines are delineated with the rpc function and respective service declaration. Meanwhile the types that the services use are declared under the message declaration. 

We can recreate the stub files using the proto: 

`python -m grpc_tools.protoc -I protos --python_out=. --pyi_out=. --grpc_python_out=. protos/chat.proto`

We now see that it is good form to have the protos file inside of a protos directory. 

## Entry 2/9/2023 9:04 pm 

In order to create an account, we have a username Unique Id, Name, password. To send messages the user has to login. We want to avoid a situation where two people request to make a username account and both will not be assigned the same id (whoever's request is sent first). My basic take is that the login token recieved should just expire after an hour and not take user activity into account. I (AM) would prefer if we implement most basic working implementation first before adding bells and whistles. 

50 characters max for every field. You can see at max 100 users. 100*50 characters passed in the list accounts operation. Regex matching for search to query relevant names. 

We have to mantain a list of the tokens that are valid, deliver to chat user either right away, or as they login. As the user logs in, we have to return a message stream. In regards, to deleting an account and generally - you have to be logged in order to to any operation such as deleting an account. Seeing that the user has to be logged in order to delete an account, they will recieve all of their undelivereed messages first. 

For the future, we want to mantain message histories, delivery confirmation and auth extension based on activity. For now we are starting with individual messages to get the server to work in the future we might add message streams.  

## Entry 2/10/2023 5:19 pm

We finalized our wire protocol standards as follows: The wire protocol encoding scheme uses an opcode and version number to determine the type of operation and support backwards compatibility. The message is encoded as a unified string buffer and decoded by parsing deliminated fields. An authentication token is required for every operation that requires the user to be logged in, which is validated by the server-side token hub upon receiving a message. The documentation also provides the message types for create account, login, message request, and list account functionalities in both wire protocol and gRPC implementation, with slight variations between the two. The documentation provides the code structure for both the wire protocol and gRPC implementation for each message type.

[Full Wire Protocol and gRPC Documentation Here](wire_design.md)


## Entry 2/12/2023 4:37 pm 

In order to create a user account we have to keep track of metadata. We opt for the twitter type inbox system where messages are just queues waiting for the user like emails. We also enable a user metadata store that keeps track of all usernames, passwords and full names. Lastly, we have a token hub which in turn provides the much needed token to timestamp mapping so we can tell when a token has expired. 


## Entry 2/13/2023 9:13 am


We ran into the following error when trying to use a forked process for the tkinter interface and the listening thread and then realized that we could not do this because the main loop object was not serializable. This came at the cost of us using python threads for the listening loop insteads of processes from Multiprocessing. 

```
Traceback (most recent call last):
  File "/Users/amishra/cs262-wire-protocol/client.py", line 184, in <module>
    run()
  File "/Users/amishra/cs262-wire-protocol/client.py", line 180, in run
    app.start()
  File "/Users/amishra/cs262-wire-protocol/client.py", line 70, in start
    mp.Process(target=self.listen_loop, daemon=True).start()
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/multiprocessing/process.py", line 121, in start
    self._popen = self._Popen(self)
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/multiprocessing/context.py", line 224, in _Popen
    return _default_context.get_context().Process._Popen(process_obj)
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/multiprocessing/context.py", line 284, in _Popen
    return Popen(process_obj)
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/multiprocessing/popen_spawn_posix.py", line 32, in __init__
    super().__init__(process_obj)
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/multiprocessing/popen_fork.py", line 19, in __init__
    self._launch(process_obj)
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/multiprocessing/popen_spawn_posix.py", line 47, in _launch
    reduction.dump(process_obj, fp)
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/multiprocessing/reduction.py", line 60, in dump
    ForkingPickler(file, protocol).dump(obj)
TypeError: cannot pickle '_tkinter.tkapp' object
```


## Entry 2/13/2023 10:32 pm 

We ran into this error when we found the tokens we were using in token hub had the incorrect datetime formatting and indexing issue. We fixed this by standardizing to UTC. 

```
Exception in thread Thread-1:
Traceback (most recent call last):
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/threading.py", line 980, in _bootstrap_inner
    self.run()
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/threading.py", line 917, in run
    self._target(*self._args, **self._kwargs)
  File "/Users/amishra/cs262-wire-protocol/client.py", line 80, in listen_loop
    for note in self.client_stub.DeliverMessages(auth_msg_request):
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/site-packages/grpc/_channel.py", line 426, in __next__
    return self._next()
  File "/Users/amishra/miniconda3/envs/262-dev/lib/python3.9/site-packages/grpc/_channel.py", line 826, in _next
    raise self
grpc._channel._MultiThreadedRendezvous: <_MultiThreadedRendezvous of RPC that terminated with:
        status = StatusCode.UNKNOWN
        details = "Exception iterating responses: 'float' object has no attribute 'total_seconds'"
        debug_error_string = "UNKNOWN:Error received from peer ipv6:%5B::1%5D:50051 {created_time:"2023-02-13T02:18:43.129338-05:00", grpc_status:2, grpc_message:"Exception iterating responses: \'float\' object has no attribute \'total_seconds\'"}"
```

## Entry 2/14/2023 4:13 pm 

We ran into several bugs with our integration testing due to deadlocks and contentions with our locking and integrity implementation. In order to solve this we removed any global locking and kept only some per object locks that have low contention. We found that three structures require access protection: user metadata store, token hub, and user inbox. The user metadata store and token hub use the `app.metadata_lock`, while the user inbox has its own lock called `app.inbox_lock`. The locking is implemented using the with pythonic syntax to ensure that the lock is not held after a function returns or a scope is unexpectedly terminated. The locking hierarchy is strictly maintained to prevent deadlocks, where the metadata lock is held first, followed by the inbox lock, and the reverse order is used to release them. Overall, the fine-grained locking approach aims to reduce contention and increase efficiency in handling concurrent requests in the chat server.

[Full Locking Documentation Here](locking_design.md)



## Entry 2/16/2023 12:00 pm

Todos: 
  - Handle GRPC errors on both client and server side
    - Check error codes on client side + show on the UI
    - Ensure no casting errors + crashing opportunities on server side
  - Integrate socket server and socket client into existing stack
    - Client disconnection should not crash server
      - Possible solutions: Timeout errors, look at the last TCP data sent
        on this connection
  - Logic for decoding
    - Client-side wire protocol
    - 4 bytes -> opcode (which dataclass the rest of this message refers to)
    - Client should ignore message if not decodable

## Entry 2/17/2023 3:30 pm 

We finished deciding on how we would implement the sockets part of the server code now that we have the grpc part done. This required us to settle for how capable our sockets server could be and we have simplified our overall design.For the gRPC setup, we have a global pool of threads that we can use to handle incomimg connections for each request. We use a RPC stream response for a client's refresh thread. This returns a blocking iterator object that in turn takes the messages that the user has not gotten and forwards them to the user. On the other hand, we have the socket implementation that does not run as a dameon thread because it is essentially polling the inbox server with a timed loop that constantly asks for refreshed messages in return for a message update per refresh. 

[Full Design Schematic](schematic.md) 

## Entry 2/18/2023 12:00 pm
For sockets, interesting problem of how we want to deal with clients violently disconnecting (by this, meaning disconnecting with no trace). We can either be constantly sending small messages back and forth between server and client once a connection is opened, and as soon as those stop being sent / received (with small timeout), we can end the connection on the server side. Or, we can have not send back and forths and instead just have a larger timeout (~60 min), such that as soon as the timeout is violated, we assume the client has "violently" disconnected and we end the connection. A 60 minute large timeout also corresponds to the liveliness of user auth tokens, although it has the con of leaving a connection open potentialsy long after it has been dead on the client side and also cutting a connection that is actually still open. It's unclear which implementation we should be using, but currently we will go with the large timeout option due to its ease of implementation.

## Entry 2/18/2023 6:00 pm
It seems like grpc automatically takes care of pairing. If two threads from the same machine each make a request, grpc will pair them correctly. I'm curious if we need to deal with the pairing in sockets. My intuition tells me no, since it seems like quite an annoying, nontrivial problem, and instead each thread / connection is given a unique port and receives a unique message.

## Entry 2/19/2023 11:00 pm
Found a bug in the UI that messages sent to an invalid recipient (aka a nonexistent username) still show up on the UI as if they were sent. We need a different message
to pop up on the UI indicating that user does not exist. Currently this bug has been verified to exist for both gRPC and socket implementations. I (RM) will fix this, 
but we will need to check to make sure the error handling is properly taken care of on the client everywhere else. We also need to potentially check the client that 
it can handle malicious messages sent to it.

It looks like only the CreateClientAccount code in the socket server was prepped to handle malicious messages, I forgot to add that to the rest of the messages. Perhaps we should be unit testing this behavior? Either way the code should be fixed now, malicious messages sent to the socket server should return an error code.

I found out that when the listening thread is not cleaned up properly then the waiting messages are not properly recieved either. 

## Entry 2/19/2023 11:30 pm

Caught a bug that allowed the socket based server to crach because the connection error was not handled well and the handler failed due to reset. We also caught a bug with concurrent accesses on deletion. Lastly, we were able to solve a couple of UI bugs that plagued our system.

We were able to solve these with our new testing framework. Our new code contains unit tests for chat server functionalities such as token generation, account creation, token verification, login, and message sending. The test suite also includes tests for account listing and deletion. Integration tests for concurrent message sending and receiving using multiple threads are also conducted. The integration tests check whether the application is able to create an account and login successfully, list the created account, send a message to another client application, and concurrently listen for incoming messages from other clients. If the integration tests pass, the function returns an integer value of 0, otherwise, an assertion error is raised, which stops the program.

[Full Testing Details](testing.md)

## Reflections on gRPC versus Wire Protocol

**Code Complexity.** The code that we wrote for the gRPC in order to get it to work was much more simplistic. Having the ability to instantly generate the stub code for serializing messages and decoding them is extremely useful. For the wire protocol, the act of packing the string buffer (or in C some memory buffer) is much more difficult. Having a struct object intialized before hand made the gRPC code more simple. Moreover, handling of where packets should go, how they should be handled and which function handles them is all taken care of. That is why we did not have to do manual connection management with sockets and manualy operation code assignment. This advantage of gRPC also contributed to simplifying our implementation as compared to the wire protocol. 

**Performance.** The ability to use streams with gRPC is super useful because the thread can then block for future messages that are sent whereas the socket implementation is left with polling. Mulitple polling refresh attempts makes the socket based wire protocol server, that we designed, unsustainable for future scaling. However, with gRPC we have the advantage of not having to use polling and the user inbox can be emptied right away as a client connects. Although we implemented a majority of this code in python, gRPC is also optimized for C buffers and the library also supports compression which can lower latency as well. In our wire-protocol, simply sending out strings is not doable in the long term. Additionally our manually encoding and decoding has lower performance as compared to protobuf's direct binary mapping. This also makes for way more efficient parsing than strings. Additionally, gRPC can handle multiple parallel requests over the same channel.

**Buffer Size.** When I compared the difference between the buffer size of the gRPC implementation and the wire protocol implementation, I found that there was a slight descrepancy. Using `ByteSize()` and `len()` for the wire protocol byte object the difference was made up for by the extra deliminating character in our buffer and the opcode assignment which made the difference of 4 bytes (100 bytes vs. 104 bytes) between the wire message and gRPC buffer size for the message "how are you doing? I hope you are well?". However, for the actual connection on the socket I send a buffer of 1024 each time and it does not fluctuate like the gRPC connection might. Therefore, the actual data that is transmitted is probably much lower for gRPC due to dynamic binary framing. Additionally another difference in the buffer size comes from the use of numbers for addressing fields rather than string field names. 