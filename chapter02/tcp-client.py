import socket

target_host = "www.google.com"
target_port = 80

# bir soket nesnesi oluştur
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# client'a bağlan
client.connect((target_host, target_port))

# biraz veri gönder
client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

# veri almak
response = client.recv(4096)

client.close()

print(response)
