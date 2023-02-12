import sys
import socket
import threading


# bu, şu adresten doğrudan alınan güzel bir hux dumping işlevidir:
# http://code.activestate.com/recipes/142812-hex-dumper/

def hexdump(src, length=16):
    result = []
    digits = 4 if isinstance(src, str) else 2

    for i in range(0, len(src), length):
        s = src[i:i + length]
        hexa = b' '.join([b"%0*X" % (digits, ord(x)) for x in s])
        text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.' for x in s])
        result.append(
            b"%04X   %-*s   %s" % (i, length * (digits + 1), hexa, text))

    print(b'\n'.join(result))


def receive_from(connection):
    buffer = b''

    # 2 saniyelik bir duraklama ayarladık.
    # Hedefinize bağlı olarak bunun ayarlanması gerekebilir
    connection.settimeout(2)

    try:

        # daha fazla veri kalmayana kadar veya
        # zaman aşımına uğrayana kadar arabelleğe okumaya devam edin
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data

    except TimeoutError:
        pass

    return buffer


# remote host'a yönelik tüm istekleri değiştirin
def request_handler(buffer):
    # paket değişiklikleri gerçekleştir
    return buffer


# local host için gönderilen tüm yanıtları değiştirin
def response_handler(buffer):
    # paket değişiklikleri gerçekleştir
    return buffer


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    # remote host'a bağlan
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    # gerekirse remote'dan veri almak
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

        # yanıt işleyicimize gönderin
        remote_buffer = response_handler(remote_buffer)

        # yerel müşterimize gönderecek verilerimiz varsa onu gönderin
        if len(remote_buffer):
            print("[<==] Sending %d bytes to localhost." % len(remote_buffer))
            client_socket.send(remote_buffer)

    # şimdi döngü yapalım ve local'den okuyalım,
    # remote'a gönderelim, local'e gönderelim tekrardan temizleyelim
    while True:
        # local host'tan oku
        local_buffer = receive_from(client_socket)

        if len(local_buffer):
            print("[==>] Received %d bytes from localhost." % len(local_buffer))
            hexdump(local_buffer)

            # istek işleyicimize gönderin
            local_buffer = request_handler(local_buffer)

            # verileri remote host'a gönder
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        # yanıtı geri almak
        remote_buffer = receive_from(remote_socket)

        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            hexdump(remote_buffer)

            # yanıt işleyicimize gönder
            remote_buffer = response_handler(remote_buffer)

            # yanıtı local socket'a gönder
            client_socket.send(remote_buffer)

            print("[<==] Sent to localhost.")

        # iki tarafta da daha fazla veri yoksa bağlantıları kapatın
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections.")
            break


def server_loop(local_host, local_port, remote_host, remote_port,
                receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((local_host, local_port))
    except socket.error as exc:
        print("[!!] Failed to listen on %s:%d" % (local_host,
                                                  local_port))
        print("[!!] Check for other listening sockets or correct "
              "permissions.")
        print(f"[!!] Caught exception error: {exc}")
        sys.exit(0)

    print("[*] Listening on %s:%d" % (local_host, local_port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # yerel bağlantı bilgilerini yazdır
        print("[==>] Received incoming connection from %s:%d" % (
            addr[0], addr[1]))

        # remote host ile bağlantı kurmak için için bir thread başlatın
        proxy_thread = threading.Thread(target=proxy_handler, args=(
            client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()


def main():
    # burada süslü komut satırı ayrımı yok
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport] [remotehost] "
              "[remoteport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)

    # yerel dinleme parametrelerini ayarla
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    # remote hedef ayarla
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    # proxy'mize remote host'a göndermeden önce bağlanmasını
    # ve veri almasını söyler.
    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False

    # şimdi dinleme soketimizi döndürün
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)


main()
