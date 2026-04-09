from socket32 import create_new_socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server
client = create_new_socket()
client.connect((HOST, PORT))

while True:
    message = client.recv(1024).decode()
    if not message:
        break

    print(message, end="")

    user_input = input()
    client.send(user_input.encode())

client.close()
