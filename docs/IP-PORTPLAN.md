# IP- og portplan

| Link | Port A | Port B | VLAN |
|---|---|---|---|
| Ansible PC–SW1 | PC NIC | SW1 Gi1/0/1 | access 99; allerede SSH-setup |
| SW1–R1 | SW1 Gi1/0/2 | R1 Gi0/0/0 | access 99 / routed management |
| SW1–R2 | SW1 Gi1/0/3 | R2 Gi0/0 | access 99 / routed management |
| R1–SW2 | R1 Gi0/0/1 | SW2 Fa0/1 | trunk 10,99 |
| R2–SW2 | R2 Gi0/1 | SW2 Fa0/2 | trunk 10,99 |
| SW2–SW3 | SW2 Fa0/3 | SW3 Gi1/0/1 | trunk 10,20,99 |
| SW3–STUD2 | Gi1/0/23-24 | STUD2-avtalte porter | Port-channel1 trunk 10,20 |
| STUD1 PC | SW3 velges senere | PC | access 10 |
| STUD2 PC | SW3 velges senere | PC | access 20 |

| Navn | IPv4 | Beskrivelse |
|---|---|---|
| PC Ansible | 192.168.99.10/24 | PC-side |
| SW1 | 192.168.99.11/24 | VLAN99 øvre |
| R1 SW1-side | 192.168.99.2/24 | SSH-bootstrap |
| R2 SW1-side | 192.168.99.3/24 | SSH-bootstrap |
| R1 SW2-side | 192.168.98.2/24 | subinterface .99 |
| R2 SW2-side | 192.168.98.3/24 | subinterface .99 |
| SW2 | 192.168.98.12/24 | VLAN99 nedre |
| SW3 | 192.168.98.13/24 | VLAN99 nedre |
| R1 VLAN10 | 192.168.10.2/24 | HSRP Active foretrukket |
| R2 VLAN10 | 192.168.10.3/24 | HSRP Standby foretrukket |
| HSRP VIP | 192.168.10.1/24 | DHCP default-router |

DHCP VLAN10: 192.168.10.50–192.168.10.199 på R1. VLAN20 og tilhørende DHCP/gateway eies av STUD2. VLAN99 går aldri over Port-channel1.
