import win32gui
import win32ui
import win32con
import win32api

# ana masaüstü penceresini bir handle'da tut
hdesktop = win32gui.GetDesktopWindow()

# tüm monitörlerin boyutunu piksel cinsinden belirleme
width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

# bir cihaz içeriği oluştur
desktop_dc = win32gui.GetWindowDC(hdesktop)
img_dc = win32ui.CreateDCFromHandle(desktop_dc)

# bellek tabanlı bir cihaz içeriği oluşturun
mem_dc = img_dc.CreateCompatibleDC()

# bir bitmap nesnesi oluştur
screenshot = win32ui.CreateBitmap()
screenshot.CreateCompatibleBitmap(img_dc, width, height)
mem_dc.SelectObject(screenshot)

# ekranı hafıza cihazı içeriğine kopyalayın
mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)

# bitmap'i bir dosyaya kaydet
screenshot.SaveBitmapFile(mem_dc, 'c:\\WINDOWS\\Temp\\screenshot.bmp')

# nesnelerimizi serbest bırakın
mem_dc.DeleteDC()
win32gui.DeleteObject(screenshot.GetHandle())
