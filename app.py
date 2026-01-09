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
import json
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import HTTPServer, SimpleHTTPRequestHandler

# ========== VARIÁVEIS GLOBAIS PARA MONITORAMENTO EM TEMPO REAL ==========
rede_estado_atual = {
    "dispositivos": [],
    "ultima_atualizacao": None,
    "rede_info": {},
    "status_global": {}
}
monitoramento_ativo = False
intervalo_ping = 5  # segundos entre cada ciclo de ping
max_threads_monitor = 4  # threads para monitoramento (menos que scan inicial)

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

def run_ping_rapido(target, timeout=500):
    """Versão otimizada do ping para monitoramento contínuo"""
    if target == "---": 
        return {"status": "---", "lat": "---", "class": "fail", "online": False}
    try:
        out = subprocess.check_output(
            ["ping", "-n", "1", "-w", str(timeout), target], 
            universal_newlines=True,
            timeout=2  # timeout do subprocess
        )
        ms = re.search(r"(\d+)ms", out)
        latencia = ms.group(0) if ms else "1ms"
        return {"status": "OK", "lat": latencia, "class": "ok", "online": True}
    except: 
        return {"status": "FALHA", "lat": "---", "class": "fail", "online": False}

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

# ========== CLASSES E FUNÇÕES PARA MONITORAMENTO EM TEMPO REAL ==========

class MonitorHandler(SimpleHTTPRequestHandler):
    """Handler HTTP para servir a interface de monitoramento e API"""
    
    def log_message(self, format, *args):
        """Suprime logs do servidor HTTP para não poluir o console"""
        pass
    
    def do_GET(self):
        # API: Retorna o status atual dos dispositivos
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(rede_estado_atual, ensure_ascii=False).encode('utf-8'))
        
        # Página principal do monitor
        elif self.path == '/' or self.path == '/monitor' or self.path == '/monitor.html':
            try:
                monitor_path = resource_path("monitor.html")
                if not os.path.exists(monitor_path):
                    # Se não existir, criar um HTML básico
                    monitor_path = "monitor.html"
                    self._criar_html_monitor()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(monitor_path, 'rb') as f:
                    self.wfile.write(f.read())
            except Exception as e:
                self.send_error(500, f"Erro ao carregar monitor: {e}")
        
        # Serve arquivos estáticos
        else:
            return SimpleHTTPRequestHandler.do_GET(self)
    
    def _criar_html_monitor(self):
        """Cria um HTML básico para monitoramento se não existir"""
        html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor de Rede em Tempo Real</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .online { background: #4CAF50; color: white; }
        .offline { background: #f44336; color: white; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #2196F3; color: white; }
        .atualizado { color: #666; font-size: 0.9em; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🌐 Monitor de Rede em Tempo Real</h1>
    <div class="atualizado">Última atualização: <span id="ultima-atualizacao">---</span></div>
    <div id="info-rede"></div>
    <h2>Dispositivos na Rede (<span id="total-dispositivos">0</span>)</h2>
    <table id="tabela-dispositivos">
        <thead><tr><th>#</th><th>IP</th><th>MAC</th><th>Hostname</th><th>Status</th><th>Latência</th></tr></thead>
        <tbody id="corpo-tabela"></tbody>
    </table>
    <script>
        function atualizarStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('ultima-atualizacao').textContent = data.ultima_atualizacao || '---';
                    document.getElementById('total-dispositivos').textContent = data.dispositivos.length;
                    
                    const tbody = document.getElementById('corpo-tabela');
                    tbody.innerHTML = '';
                    data.dispositivos.forEach((d, i) => {
                        const tr = document.createElement('tr');
                        const statusClass = d.online ? 'online' : 'offline';
                        const statusText = d.online ? '✓ Online' : '✗ Offline';
                        tr.innerHTML = `
                            <td>${i+1}</td>
                            <td>${d.ip}</td>
                            <td>${d.mac}</td>
                            <td>${d.hostname}</td>
                            <td class="${statusClass}">${statusText}</td>
                            <td>${d.latencia || '---'}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                })
                .catch(e => console.error('Erro ao buscar status:', e));
        }
        
        // Atualiza a cada 3 segundos
        setInterval(atualizarStatus, 3000);
        atualizarStatus();
    </script>
</body>
</html>"""
        with open("monitor.html", "w", encoding="utf-8") as f:
            f.write(html_content)


def loop_monitoramento():
    """Loop principal de monitoramento que roda em thread separada"""
    global rede_estado_atual, monitoramento_ativo
    
    print("[Monitor] Thread de monitoramento iniciada")
    
    while monitoramento_ativo:
        try:
            dispositivos_atualizados = []
            dispositivos_atuais = rede_estado_atual.get("dispositivos", [])
            
            if not dispositivos_atuais:
                print("[Monitor] Nenhum dispositivo para monitorar. Aguardando...")
                time.sleep(intervalo_ping)
                continue
            
            # Função para verificar um dispositivo
            def verificar_dispositivo(device):
                status = run_ping_rapido(device['ip'], timeout=500)
                return {
                    "ip": device['ip'],
                    "mac": device.get('mac', '---'),
                    "hostname": device.get('hostname', '---'),
                    "status": status['status'],
                    "latencia": status['lat'],
                    "online": status['online'],
                    "class": status['class']
                }
            
            # Usa ThreadPool com limite de threads para não sobrecarregar
            with ThreadPoolExecutor(max_workers=max_threads_monitor) as executor:
                futures = [executor.submit(verificar_dispositivo, d) for d in dispositivos_atuais]
                for future in as_completed(futures):
                    try:
                        resultado = future.result()
                        dispositivos_atualizados.append(resultado)
                    except Exception as e:
                        print(f"[Monitor] Erro ao verificar dispositivo: {e}")
            
            # Atualiza o estado global
            rede_estado_atual["dispositivos"] = sorted(
                dispositivos_atualizados, 
                key=lambda x: [int(n) for n in x["ip"].split(".")]
            )
            rede_estado_atual["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Aguarda antes do próximo ciclo
            time.sleep(intervalo_ping)
            
        except Exception as e:
            print(f"[Monitor] Erro no loop de monitoramento: {e}")
            time.sleep(intervalo_ping)
    
    print("[Monitor] Thread de monitoramento encerrada")


def iniciar_monitoramento(dispositivos, rede_info):
    """Inicia o monitoramento em tempo real"""
    global rede_estado_atual, monitoramento_ativo
    
    # Prepara o estado inicial
    rede_estado_atual["dispositivos"] = [
        {
            "ip": d['ip'],
            "mac": d.get('mac', '---'),
            "hostname": d.get('hostname', '---'),
            "online": True,
            "status": "OK",
            "latencia": "---",
            "class": "ok"
        } for d in dispositivos
    ]
    rede_estado_atual["rede_info"] = rede_info
    rede_estado_atual["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Inicia a thread de monitoramento
    monitoramento_ativo = True
    thread_monitor = threading.Thread(target=loop_monitoramento, daemon=True)
    thread_monitor.start()
    
    print(f"\n{'='*60}")
    print("🔴 MONITOR EM TEMPO REAL ATIVO")
    print(f"{'='*60}")
    print(f"📊 Monitorando {len(dispositivos)} dispositivos")
    print(f"⏱️  Intervalo de atualização: {intervalo_ping} segundos")
    print(f"🌐 Acesse: http://localhost:8000")
    print(f"{'='*60}\n")
    
    # Inicia o servidor HTTP
    try:
        httpd = HTTPServer(('0.0.0.0', 8000), MonitorHandler)
        print("✅ Servidor web rodando. Pressione Ctrl+C para parar.")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[Monitor] Encerrando servidor...")
        monitoramento_ativo = False
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")
        monitoramento_ativo = False


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
        print(f"Erro ao gerar relatório: {e}")
    
    # Pergunta se o usuário quer ativar o monitoramento em tempo real
    print(f"\n{'='*60}")
    print("📊 SCAN COMPLETO!")
    print(f"Dispositivos encontrados: {len(devices)}")
    print(f"{'='*60}\n")
    
    resposta = input("Deseja ativar o monitoramento em tempo real? (s/n): ").strip().lower()
    
    if resposta in ['s', 'sim', 'y', 'yes']:
        iniciar_monitoramento(devices, net)
    else:
        print("Programa finalizado.")

if __name__ == "__main__":
    main()