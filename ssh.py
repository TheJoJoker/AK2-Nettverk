import serial
import time
from getpass import getpass

port = input('Konsollport (f.eks. /dev/ttyUSB0 eller COM3): ')
type_device = input('Router (R) eller switch (S): ').strip().upper()
hostname = input('Hostname: ').strip()
interface = input('Management-interface (f.eks. Gi0/0 eller Vlan99): ').strip()
ip = input('IP og nettmaske (f.eks. 192.168.99.2 255.255.255.0): ').strip()
username = input('SSH-bruker [cisco]: ').strip() or 'cisco'
password = getpass('SSH-passord: ')
enable_password = getpass('Enable-passord: ')

commands = ['', 'enable', 'configure terminal', f'hostname {hostname}']

if type_device == 'S':
    vlan = input('Management-VLAN [99]: ').strip() or '99'
    gateway = input('Default gateway (valgfritt): ').strip()
    commands += [f'vlan {vlan}', 'exit']
    # På en L2-switch skal management-IP settes på VLAN-interfacet.
    commands += [f'interface Vlan{vlan}', f'ip address {ip}', 'no shutdown', 'exit']
    if gateway:
        commands.append(f'ip default-gateway {gateway}')
    if interface.lower() != f'vlan{vlan}'.lower():
        mode = input('Portmodus (access/trunk/skip) [skip]: ').strip().lower() or 'skip'
        if mode == 'access':
            commands += [f'interface {interface}', 'switchport mode access',
                         f'switchport access vlan {vlan}', 'no shutdown', 'exit']
        elif mode == 'trunk':
            allowed = input('Tillatte VLAN (f.eks. 10,20,99): ').strip()
            commands += [f'interface {interface}', 'switchport mode trunk',
                         f'switchport trunk allowed vlan {allowed}', 'no shutdown', 'exit']
elif type_device == 'R':
    commands += [f'interface {interface}', f'ip address {ip}', 'no shutdown', 'exit']
else:
    raise SystemExit('Velg R eller S')

commands += [
    'ip domain name ak2.local',
    f'username {username} privilege 15 secret {password}',
    f'enable secret {enable_password}',
    'crypto key generate rsa modulus 2048',
    'ip ssh version 2',
    'line vty 0 4',
    'login local',
    'transport input ssh',
    'exit',
    'end',
]

with serial.Serial(port, 9600, timeout=2) as console:
    for command in commands:
        console.write((command + '\r\n').encode())
        time.sleep(1)
        print(console.read(console.in_waiting or 1).decode(errors='replace'), end='')

print('\nSjekk konsollutskriften for feil før du lagrer med "write memory".')
