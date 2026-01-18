#!/usr/bin/env python3
"""Test SSH connection to myCobot Pi"""
import paramiko

host = '192.168.55.1'
credentials = [
    ('pi', 'raspberry'),
    ('pi', 'elephant'),
    ('pi', 'Elephant'),
    ('ubuntu', 'ubuntu'),
    ('er', 'elephant'),
    ('er', 'Elephant'),
    ('root', 'raspberry'),
    ('root', 'elephant'),
]

print(f'Attempting SSH to {host}...')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

connected = False
for user, pwd in credentials:
    try:
        print(f'  Trying {user}:{pwd}...', end=' ')
        client.connect(host, username=user, password=pwd, timeout=5)
        print('SUCCESS!')
        connected = True
        
        # Run a test command
        stdin, stdout, stderr = client.exec_command('hostname && uname -a')
        output = stdout.read().decode()
        print(f'\n  System Info: {output.strip()}')
        
        # Check for pymycobot
        stdin, stdout, stderr = client.exec_command('python3 -c "import pymycobot; print(pymycobot.__version__)"')
        output = stdout.read().decode()
        err = stderr.read().decode()
        if output:
            print(f'  pymycobot version: {output.strip()}')
        else:
            print(f'  pymycobot: {err.strip()[:80]}')
        
        # Try to read robot angles
        print('\n  Attempting to read robot angles on Pi...')
        cmd = '''python3 -c "
from pymycobot import MyCobot
import time
mc = MyCobot('/dev/ttyAMA0', 1000000)
time.sleep(0.5)
print('angles:', mc.get_angles())
"'''
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode()
        err = stderr.read().decode()
        if output:
            print(f'  {output.strip()}')
        if err:
            print(f'  Error: {err.strip()[:100]}')
        
        client.close()
        break
    except paramiko.AuthenticationException:
        print('wrong password')
    except Exception as e:
        print(f'error: {str(e)[:50]}')

if not connected:
    print('\nCould not authenticate with default credentials.')
    print('Check your myCobot documentation for the correct password.')
