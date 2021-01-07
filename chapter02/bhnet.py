import sys
import socket
import getopt
import threading
import subprocess
import argparse

args = None

def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((args.target, args.port))

        if len(buffer):
            client.send(buffer.encode())
    
        while True:
            recv_len = 1
            response = b""

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data

                if recv_len < 4096:
                    break

            print(response.decode(), end=' ')

            buffer = input("")
            buffer += "\n"
            
            client.send(buffer.encode())
    
    except socket.error as exc:
        print("[*] Exception! Exiting!")
        print(exc)
        client.close()


def server_loop():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((args.target, args.port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()


def run_command(command):
    command = command.rstrip()

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command. \r\n"
    
    return output


def client_handler(client_socket):
    if args.upload_destination:
        file_buffer = ""
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data
        
        try:
            file_d = open(args.upload_destination, "wb")
            file_d.write(file_buffer.encode())
            file_d.close()
            client_socket.send("Successfully saved file to {}".format(args.upload_destination))
        except:
            client_socket.send("Failed to save file to {}".format(args.upload_destination))

    if args.execute:
        output = run_command(args.execute)
        client_socket.send(output)

    if args.command:
        while True:
            client_socket.send(b"<PyCat:#> ")
            cmd_buffer = b""
            while b"\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
            
            response = run_command(cmd_buffer)
            client_socket.send(response)


def main():
    global args

    parser = argparse.ArgumentParser(description="Python Netcat Tool")
    parser.add_argument("-l", "--listen", action="store_true")
    parser.add_argument("-c", "--command", action="store_true")
    parser.add_argument("-e", "--execute", action="store", type=str)
    parser.add_argument("-t", "--target", action="store", type=str, default="0.0.0.0")
    parser.add_argument("-p", "--port", action="store", type=int)
    parser.add_argument("-u", "--upload_destination", action="store", type=str)

    args = parser.parse_args()

    if not args.target or not args.port:
        print("Target and Port Number Required!!!")
        sys.exit(0)

    if not args.listen and args.target and args.port > 0:
        buffer = sys.stdin.read()
        client_sender(buffer)

    if args.listen:
        server_loop()


main()