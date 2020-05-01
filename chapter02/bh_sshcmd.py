import paramiko


def ssh_command(ip, user, passwd, command):
    client = paramiko.SSHClient()
    # client can also support using key files
    # client.load_host_keys('/home/user/.ssh/known_hosts')
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=passwd)
    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        ssh_session.exec_command(command)
        print(ssh_session.recv(1024))
    return


ssh_command('192.168.100.131', 'justin', 'lovesthepython', 'ClientConnected')
