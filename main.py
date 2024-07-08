from threading import Thread
from pathlib import Path
import argparse
import socket

def generate_response(response, path):
    content_length = len(path)
    response += str(content_length).encode()
    response += b"\r\n\r\n"
    response += bytes(path, 'utf-8')
    response += b"\r\n"
    return response

def handle_connection(server_socket, directory):

    res_200 = b"HTTP/1.1 200 OK\r\n\r\n"
    res_400 = b"HTTP/1.1 404 Not Found\r\n\r\n"
    res_random_string = (b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: ")

    connection, _ = server_socket.accept() # wait for client
    
    received_bytes = connection.recv(4096).decode("utf-8")
    user_agent = received_bytes.split("\r\n")[2]
    request_method = received_bytes.split("\r\n")[0].split()[0]
    print(request_method)
    path = received_bytes.split("\r\n")[0].split()[1]

    if path == "/":
        connection.send(res_200)

    elif path.startswith('/echo/'):
        real_path = path[6:]
        res_random_string = generate_response(res_random_string, real_path)
        connection.send(res_random_string)

    elif path.startswith('/user-agent'):
        real_path = user_agent.split()[1]
        res_random_string = generate_response(res_random_string, real_path)
        connection.send(res_random_string)

    elif (path.startswith('/files/')) and request_method == 'POST':
        filename = path.removeprefix('/files/')
        filepath = Path(directory)/filename
        file_content = received_bytes.split("\r\n\r\n")[1]
        with filepath.open("w") as f:
            f.write(file_content)
        connection.send(b"HTTP/1.1 201 File created\r\n\r\n")

    elif path.startswith('/files/'):
        filename = path.removeprefix('/files/')
        filepath = Path(directory)/filename
        if filepath.exists():
            with filepath.open() as f:
                content = f.read()
                connection.send(
                    "\r\n".join(
                        [
                            "HTTP/1.1 200 OK",
                            "Content-Type: application/octet-stream",
                            "Content-Length: " + str(len(content)),
                            "",
                            content,
                        ]
                    ).encode("utf-8")
                )
        else:
            connection.send(res_400)
    else:
        connection.send(res_400)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory")
    args = parser.parse_args()
    print(args)
    directory = args.directory
    server_socket = socket.create_server(("localhost", 4221))
    threads = []
    for _ in range(16):
        thread = Thread(target=handle_connection, args=[server_socket, directory])
        threads.append(thread)
        thread.start()

    [thread.join() for thread in threads]
    server_socket.close()

if __name__ == "__main__":
    main()
