import os


def run():
    print("[*] In dirlister module.")
    files = os.listdir(".")

    return str(files)
