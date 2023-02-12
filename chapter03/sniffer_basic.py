import socket
import os

# host için dinleme adresi
host = "192.168.0.196"

# ham bir soket oluşturun ve onu ortak arayüze bağlayın
if os.name == "nt":
    socket_protocol = socket.IPPROTO_IP
else:
    socket_protocol = socket.IPPROTO_ICMP

sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol) 

sniffer.bind((host, 0))

# yakalamaya dahil edilen IP başlıklarını istiyoruz
sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# Windows kullanıyorsak promiscuous modunu kurmak için
# bir IOCTL göndermemiz gerekir
if os.name == "nt": 
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

# tek bir pakette okumak
print(sniffer.recvfrom(65535))

# Windows'taysak promiscuous modunu kapat
if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
