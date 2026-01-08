import socket
import uuid
import platform
import subprocess
import webbrowser
import os
import sys
import getpass
import re
import ipaddress
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Garante que o EXE encontre o HTML interno
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_uptime():
    try:
        # Comando para Windows pegar o tempo de atividade
        output = subprocess.check_output("net statistics workstation", shell=True).decode('cp850')
        match = re.search(r"desde (.*)", output)
        return match.group(1).strip() if match else "Não disponível"
    except: return "Não disponível"

def get_router_mac(gateway_ip):
    if not gateway_ip or gateway_ip in ["---", "0.0.0.0", "Não encontrado"]:
        return "Não identificado"
    try:
        # Ping rápido para garantir que o roteador responda ao ARP
        subprocess.run(["ping", "-n", "1", "-w", "700", gateway_ip], capture_output=True, text=True)
        # Lê a tabela ARP do Windows
        arp_out = subprocess.check_output(f"arp -a {gateway_ip}", shell=True).decode('cp850')
        # Regex para capturar o MAC
        mac_match = re.search(r"([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})", arp_out)
        if mac_match:
            return mac_match.group(1).replace('-', ':').upper()
    except: pass
    return "Não encontrado"

def get_network_details():
    net = {"gw": "---", "ip": "---", "dns": "---", "interface": "Desconhecida"}
    try:
        # Pega Gateway e IP local via tabela de rotas (o método mais preciso)
        route = subprocess.check_output("route print 0.0.0.0", shell=True).decode('cp850')
        for line in route.splitlines():
            if "0.0.0.0" in line and "Metrica" not in line:
                parts = line.split()
                if len(parts) >= 4:
                    net["gw"] = parts[2]; net["ip"] = parts[3]
                    break
        
        # Pega detalhes do adaptador (DNS e Tipo)
        ipconfig = subprocess.check_output("ipconfig /all", shell=True).decode('cp850')
        adapters = ipconfig.split("\n\n")
        for adapter in adapters:
            if net["ip"] in adapter:
                net["interface"] = "Wi-Fi 📶" if "Wi-Fi" in adapter or "Wireless" in adapter else "Ethernet 🔌"
                dns_match = re.search(r"Servidores DNS.*: ([\d\.]+)", adapter)
                if dns_match: net["dns"] = dns_match.group(1)
    except: pass
    return net

def run_ping(target):
    if target == "---": return {"status": "---", "lat": "---", "class": "fail"}
    try:
        out = subprocess.check_output(["ping", "-n", "1", "-w", "1000", target], universal_newlines=True)
        ms = re.search(r"(\d+)ms", out)
        return {"status": "OK", "lat": ms.group(0) if ms else "1ms", "class": "ok"}
    except: return {"status": "FALHA", "lat": "---", "class": "fail"}

def get_mac_from_arp(ip):
    """Obtém o MAC address de um IP via ARP"""
    try:
        subprocess.run(["ping", "-n", "1", "-w", "300", ip], capture_output=True, text=True)
        arp_out = subprocess.check_output(f"arp -a {ip}", shell=True).decode('cp850')
        mac_match = re.search(r"([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})", arp_out)
        if mac_match:
            return mac_match.group(1).replace('-', ':').upper()
    except: pass
    return None

def scan_network(network_ip):
    """Escaneia a rede e retorna lista de dispositivos ativos"""
    devices = []
    try:
        network = ipaddress.ip_network(network_ip, strict=False)
        ips = [str(ip) for ip in network.hosts()]
        
        def check_host(ip):
            try:
                subprocess.run(["ping", "-n", "1", "-w", "300", ip], capture_output=True, text=True, timeout=2)
                mac = get_mac_from_arp(ip)
                if mac:
                    hostname = "---"
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except:
                        pass
                    return {"ip": ip, "mac": mac, "hostname": hostname}
            except:
                pass
            return None
        
        # 6 threads é o ideal para não travar
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(check_host, ip) for ip in ips]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    devices.append(result)
        
        devices.sort(key=lambda x: [int(n) for n in x["ip"].split(".")])
    except Exception as e:
        print(f"Erro ao escanear rede: {e}")
    
    return devices

def main():
    print("Iniciando varredura técnica... Aguarde.")
    net = get_network_details()
    p_gw = run_ping(net["gw"])
    p_net = run_ping("8.8.8.8")
    
    try:
        socket.gethostbyname("google.com")
        dns_res = {"status": "OK", "class": "ok"}
    except:
        dns_res = {"status": "FALHA", "class": "fail"}

    # Escaneia a rede local
    print("Escaneando rede local... Isto pode levar alguns minutos.")
    network_range = net["ip"].rsplit(".", 1)[0] + ".0/24"
    devices = scan_network(network_range)

    # Gera tabela HTML dos dispositivos
    devices_html = ""
    for i, device in enumerate(devices, 1):
        devices_html += f"""
        <tr>
            <td>{i}</td>
            <td>{device['ip']}</td>
            <td>{device['mac']}</td>
            <td>{device['hostname']}</td>
        </tr>
        """

    context = {
        "{{time}}": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "{{uptime}}": get_uptime(),
        "{{hostname}}": socket.gethostname(),
        "{{user}}": getpass.getuser(),
        "{{mac}}": ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(40, -1, -8)]).upper(),
        "{{ip}}": net["ip"],
        "{{gateway}}": net["gw"],
        "{{mac_router}}": get_router_mac(net["gw"]),
        "{{dns}}": net["dns"],
        "{{interface}}": net["interface"],
        "{{status_gw}}": p_gw["status"], "{{lat_gw}}": p_gw["lat"], "{{class_gw}}": p_gw["class"],
        "{{status_net}}": p_net["status"], "{{lat_net}}": p_net["lat"], "{{class_net}}": p_net["class"],
        "{{status_dns_test}}": dns_res["status"], "{{class_dns_test}}": dns_res["class"],
        "{{devices_table}}": devices_html,
        "{{devices_count}}": str(len(devices))
    }

    try:
        template_path = resource_path("report_template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        for k, v in context.items():
            html = html.replace(k, str(v))

        report_name = "diagnostico_rede.html"
        with open(report_name, "w", encoding="utf-8") as f:
            f.write(html)
        
        webbrowser.open("file://" + os.path.abspath(report_name))
        print("Relatório gerado com sucesso!")
    except Exception as e:
        print(f"Erro fatal: {e}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()