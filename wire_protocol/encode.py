def AccountCreateRequest(version, username, password, fullname):
    opcode = 0
    return f"{opcode}||{version}||{username}||{password}||{fullname}".encode("ascii")

def AccountCreateReply(version, error_code, auth_token, fullname):
    opcode = 0
    return f"{opcode}||{version}||{error_code}||{auth_token}||{fullname}".encode("ascii")

def LoginRequest(version, username, password):
    opcode = 1
    return f"{opcode}||{version}||{username}||{password}".encode("ascii")

def LoginReply(version, error_code, auth_token, fullname):
    opcode = 1
    return f"{opcode}||{version}||{error_code}||{auth_token}||{fullname}".encode("ascii")

def MessageRequest(version, auth_token, username, recipient_username, message):
    opcode = 2
    return f"{opcode}||{version}||{auth_token}||{username}||{recipient_username}||{message}".encode("ascii")

def MessageReply(version, error_code):
    opcode = 2
    return f"{opcode}||{version}||{error_code}".encode("ascii")

def ListAccountRequest(version, auth_token, username, number_of_accounts, regex):
    opcode = 3
    return f"{opcode}||{version}||{auth_token}||{username}||{number_of_accounts}||{regex}".encode("ascii")

def ListAccountReply(version, error_code, account_names):
    opcode = 3
    return f"{opcode}||{version}||{error_code}||{account_names}".encode("ascii")

def DeleteAccountRequest(version, auth_token, username):
    opcode = 4
    return f"{opcode}||{version}||{auth_token}||{username}".encode("ascii")

def DeleteAccountReply(version, error_code):
    opcode = 4
    return f"{opcode}||{version}||{error_code}".encode("ascii")

def RefreshRequest(version, auth_token, username):
    opcode = 5
    return f"{opcode}||{version}||{auth_token}||{username}".encode("ascii")

def RefreshReply(version, message, error_code):
    opcode = 5
    return f"{opcode}||{version}||{message}||{error_code}".encode("ascii")

def ServerStatusUpdate(version, port, position):
    opcode = 6
    return f"{opcode}||{version}||{port}||{position}".encode("ascii")

def ServerElectionTrigger(version):
    opcode = 7
    return f"{opcode}||{version}".encode("ascii")

def ServerElectionBallot(version, port, value):
    opcode = 8
    return f"{opcode}||{version}||{port}||{value}".encode("ascii")

def ServerSendState(version, state):
    opcode = 9
    return f"{opcode}||{version}||{state}".encode("ascii")