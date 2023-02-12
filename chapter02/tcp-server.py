import socket
import threading

bind_ip = "0.0.0.0"
bind_port = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((bind_ip, bind_port))

server.listen(5)

print("[*] Listening on %s:%d" % (bind_ip, bind_port))


# bu bizim client handling thread'imiz
def handle_client(client_socket):
    # sadece client'ın ne gönderdiğini yazdırın
    request = client_socket.recv(1024)

    print("[*] Received: %s" % request)

    # bir paketi geri gönder
    client_socket.send(b"ACK!")
    print(client_socket.getpeername())
    client_socket.close()


while True:
    client, addr = server.accept()

    print("[*] Accepted connection from: %s:%d" % (addr[0], addr[1]))

    # gelen verileri işlemek için client thread'ı döndürün
    client_handler = threading.Thread(target=handle_client, args=(client,))
    client_handler.start()
