import socket
import struct

def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection Closed")
        data += chunk
    return data

# function to send header and payload
def send_message(sock, message_type, payload):
    header = struct.pack("!BI", message_type, len(payload))
    sock.sendall(header)
    sock.sendall(payload)

# function to receive message type and payload
def recv_message(sock):
    header = recv_exact(sock, 5)
    msg_type, payload_len = struct.unpack("!BI", header)
    payload = recv_exact(sock, payload_len)
    return (msg_type, payload)