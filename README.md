# STUD1 – Nettverksautomatisering med Ansible
Dette prosjektet automatiserer konfigurasjonen av et fysisk Cisco-nettverk ved hjelp av Ansible og Python.
Nettverket består av 3 swither og to rutere.
De to ruterne bruker HSRP for å gi en redundant gateway til VLAN 10 (STUD1). R1 fungerer som primærruter og DHCP-server, mens R2 fungerer som reserveruter. 
VLAN 20 tilhører STUD2 og transporteres mellom studentenes nettverk gjennom en EtherChannel med LACP mellom SW3-switchene. VLAN 99 brukes til management og sendes ikke over EtherChannel.
IP og portplan ligger under /docs/IP-PORTPLAN.md

## SSH og automatisering
Først brukes et enkelt Python-script med pySerial og konsollkabel for å konfigurere management-IP, SSH-bruker og SSH-tilgang på hver Cisco-enhet.
Deretter brukes Ansible med cisco.ios-collection og Paramiko til å konfigurere resten av nettverket, inkludert porter, VLAN, trunker, HSRP, DHCP og EtherChannel. Paramiko brukes for kompatibilitet med eldre Cisco-utstyr (Dette fungerer ikke, så eldre utstyr for man feil ved kjøring av ansible).
Alle fem enhetene administreres fra én Linux-maskin via SSH. IP-adresser, porter og VLAN er definert i felles variabelfiler, slik at konfigurasjonen er enkel å gjenbruke, endre og vedlikeholde.

## Enheter
- SW1: SSH 192.168.99.11, Gi1/0/1 til Ansible-PC er allerede konfigurert.
- R1: SSH 192.168.99.2, Gi0/0/0 er allerede konfigurert.
- R2: SSH 192.168.99.3, Gi0/0/0 er allerede konfigurert.
- SW2: SSH 192.168.98.12, antatt Fa0/1 allerede satt via SSH-scriptet.
- SW3: SSH 192.168.98.13, antatt Gi1/0/1 allerede satt via SSH-scriptet.

## Ikke fungerende enheter
Disee enhetene vil ikke fungere da de bruker gammelt RSA oppsett.
- ISR 2901
- Catalyst 2960
- Catalyst 1000

# Oppsett guide
Dette er en gjennomgang av alle kommandoene og rekkefølgen for å komplett sette opp miljøet.

## Sett opp SSH på alle enhetene
Før Ansible kan konfigurere nettverket, må SSH aktiveres på alle Cisco-enhetene. Dette gjøres med Python-scriptet ssh.py via konsollkabel.
Scriptet bruker pySerial til å koble seg til Cisco-enhetene og konfigurerer hostname, management-IP, SSH-bruker, passord og SSH-tilgang.

## 1. SSH-konfigurasjon for hver enhet

SSH settes opp **før** Ansible, ved å koble konsollkabel til én enhet om gangen og kjøre `ssh.py`. Skriptet konfigurerer kun den valgte management-porten, management-IP og SSH. De øvrige portene, VLAN-trunkene, HSRP, DHCP og EtherChannel konfigureres senere med Ansible.

| Enhet | Valg i skriptet | Interface / fysisk port | Management-IP og maske | VLAN / portmodus |
|---|---|---|---|---|
| SW1 | `S` | `GigabitEthernet1/0/1` | `192.168.99.11 255.255.255.0` på `Vlan99` | VLAN 99, `access` |
| R1 | `R` | `GigabitEthernet0/0/0` | `192.168.99.2 255.255.255.0` | Ingen switchport-modus |
| R2 | `R` | `GigabitEthernet0/0` | `192.168.99.3 255.255.255.0` | Ingen switchport-modus |
| SW2 | `S` | `FastEthernet0/1` | `192.168.98.12 255.255.255.0` på `Vlan99` | VLAN 99, `trunk`, tillat `10,99` |
| SW3 | `S` | `GigabitEthernet1/0/1` | `192.168.98.13 255.255.255.0` på `Vlan99` | VLAN 99, `trunk`, tillat `10,20,99` |

**Merk:** På switchene legges management-IP på det logiske interfacet `Vlan99`, ikke på den fysiske porten. SW2- og SW3-portene må faktisk transportere VLAN 99 for at SSH skal bli tilgjengelig fra management-nettet.

### 2. Start SSH-skriptet

Installer pySerial og kjør skriptet mens konsollkabelen er tilkoblet:

```bash
pip install pyserial
python3 ssh.py
```

Velg riktig konsollport (for eksempel `/dev/ttyUSB0` eller `COM3`), `R` for ruter eller `S` for switch, og fyll inn verdiene i tabellen. Bruk gjerne `cisco` som SSH-brukernavn på alle enhetene. Velg SSH-passord og enable secret selv. Skriptet bruker domenet `ak2.local` og forsøker å aktivere SSH versjon 2 med RSA-nøkler; faktisk støtte avhenger av IOS-versjonen.

For switchenes default gateway brukes:

| Enhet | Default gateway ved førstegangsoppsett |
|---|---|
| SW1 | Ikke nødvendig for SSH fra Ansible-PC i samme subnett |
| SW2 | `192.168.98.2` (R1 mot SW2) |
| SW3 | `192.168.98.2` (R1 mot SW2) |

### 3. Test SSH

Fra Ansible-PC-en:

```bash
ssh ansible@192.168.99.11  # SW1
ssh ansible@192.168.99.2   # R1
ssh ansible@192.168.99.3   # R2
ssh ansible@192.168.98.12  # SW2
ssh ansible@192.168.98.13  # SW3
```

SW2 og SW3 vil først kunne nås fra Ansible-PC-en når forbindelsene, VLAN 99 og rutingen til `192.168.98.0/24` fungerer. R1 og R2 vil kunne nås når SW1 er konfigurert. En vellykket kjøring av SSH-skriptet betyr derfor ikke nødvendigvis at alle fem enhetene er tilgjengelige over nettverket. Sjekk konsollutskriften for kommandofeil og test innlogging før konfigurasjonen lagres.

Ansible bruker deretter `cisco.ios` og tilkoblingsinnstillingene i `ansible.cfg`. Dersom eldre enheter ikke støtter algoritmene SSH-klienten tilbyr, må dette undersøkes særskilt; Paramiko alene garanterer ikke kompatibilitet.


## Installering
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ansible-core paramiko
ansible-galaxy collection install -r requirements.yml
```

## Variabler og Paramiko – ett sted
- **Alle porter, VLAN og IP-er:** `inventory/group_vars/all.yml` (ikke en ekstra `group_vars/all.yml` i rot).
- **Alle tilkoblingsadresser/bruker:** `inventory/hosts.yml`.
- **Paramiko for network_cli:** `ansible.cfg` under `[persistent_connection]`, `ssh_type = paramiko`.
- Bruk kommandoene fra **prosjektroten**, og inkluder alltid `-i inventory/hosts.yml`for å sikkre at inventoryfilen blir kjørt rikitg.
- Ikke sjekk inn passord. Bruk `--ask-pass --ask-become-pass`; med privilege 15 er enable ofte ikke nødvendig, men metoden krever det ved behov.

Sjekk alltid:
```bash
ansible-config dump --only-changed
ansible-inventory -i inventory/hosts.yml --host SW1 --yaml
ansible-playbook -i inventory/hosts.yml playbooks/01_sw1.yml --syntax-check
```
Du **skal** se `ports:` i inventory-utskriften.

## Sikker fremgangsmåte
**Første kontroll – les, ingen endringer:**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/00_preflight.yml --limit SW1 --ask-pass --ask-become-pass
```
Hvis denne fungerer, aktiver øvrige SW1-porter og nedre router-subinterfaces:
```bash
ansible-playbook -i inventory/hosts.yml playbooks/01_sw1.yml --ask-pass --ask-become-pass
ansible-playbook -i inventory/hosts.yml playbooks/02_routers.yml --ask-pass --ask-become-pass
```
På Ansible-PC (Linux):
```bash
sudo ip route add 192.168.98.0/24 via 192.168.99.2
```
Hvis ruta allerede finnes bruk `ip route show`; Linux gir 'File exists' ved duplikat.

**Sjekk først at SW2 og SW3 svarer via SSH**, og prøv lesetesten per switch:
```bash
ansible-playbook -i inventory/hosts.yml playbooks/00_preflight.yml --limit SW2 --ask-pass --ask-become-pass
ansible-playbook -i inventory/hosts.yml playbooks/00_preflight.yml --limit SW3 --ask-pass --ask-become-pass
```
Når SW2 er tilgjengelig: 
```bash
ansible-playbook -i inventory/hosts.yml playbooks/03_sw2.yml --ask-pass --ask-become-pass
ansible-playbook -i inventory/hosts.yml playbooks/04_sw3.yml --ask-pass --ask-become-pass
```
**Ikke kjør playbook 03 eller 04 hvis du står i fare for å endre den eneste fungerende management-porten midt i en SSH-økt.** Ved førstegangsoppsett med bare én fysisk port er det mulig at du må bruke konsoll eller en midlertidig tilgang for bootstrap. SW2 Fa0/1 og SW3 Gi1/0/1 er del av trunk-konfigurasjonen – kontroller VLAN99 etterpå.

```bash
ansible-playbook -i inventory/hosts.yml playbooks/05_pc_ports.yml --ask-pass --ask-become-pass
ansible-playbook -i inventory/hosts.yml playbooks/06_etherchannel.yml --ask-pass --ask-become-pass
```
På begge sider av STUD2-LACP må oppsettet være kompatibelt; ingen VLAN99 over denne forbindelsen. Før endringer på medlemsporter: sjekk at de ikke brukes til annet og ikke står i en tidligere port-channel.

Til slutt:
```bash
ansible-playbook -i inventory/hosts.yml playbooks/07_verify.yml --ask-pass --ask-become-pass
ansible-playbook -i inventory/hosts.yml playbooks/08_save.yml --ask-pass --ask-become-pass
```

## Ting du må verifisere i fysisk lab
1. Koble opp kalbing ut i fra IP-plan.
2. Om noen av enhetene bruker gammelt RSA oppsett.
