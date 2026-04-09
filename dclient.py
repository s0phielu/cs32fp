import socket

HOST = "127.0.0.1"
PORT = 65432

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

while True:
    message = client.recv(1024).decode()

    if not message:
        break

    print(message, end="")

    user_input = input()
    client.send(user_input.encode())

client.close()
