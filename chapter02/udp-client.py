import socket

target_host = "127.0.0.1"
target_port = 80

# bir soket nesnesi oluştur
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# biraz veri gönder
client.sendto(b"AAABBBCCC", (target_host, target_port))

# biraz veri al
data, addr = client.recvfrom(4096)

client.close()

print(data)
