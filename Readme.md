# 📡 Real-Time Network Monitor & Scanner

![Python](https://img.shields.io/badge/Python-Standard_Lib-3776AB?logo=python&logoColor=white)
![HTML5](https://img.shields.io/badge/Frontend-HTML5%20%2B%20JS-E34F26?logo=html5&logoColor=white)
![Status](https://img.shields.io/badge/Status-Realtime-success)

> **Uma evolução do scanner de rede tradicional para uma ferramenta de monitoramento contínuo em tempo real via navegador.**

## 📖 Sobre o Projeto
Este projeto é um **Fork aprimorado** do *Network Scanner* original. Enquanto a versão original foca em diagnósticos pontuais ("snapshots"), esta versão introduz uma arquitetura **Cliente-Servidor** para monitorar a disponibilidade e latência de dispositivos na rede corporativa 24/7.

### ⚡ Principais Evoluções (Diferenças desta versão)
| Característica | Versão Original | 🟢 Minha Versão (Monitor) |
| :--- | :--- | :--- |
| **Execução** | Script único (Roda e Fecha) | **Servidor Contínuo (Daemon)** |
| **Interface** | HTML Estático | **Dashboard Dinâmico (Auto-Refresh)** |
| **Alcance** | Host Local + Gateway | **Varredura Completa de Subnet** |
| **Arquitetura** | Linear (Single-Thread) | **Multithreading + HTTP Server** |
| **Alerta** | N/A | **Visual (Pisca em Vermelho)** |

---

## 🚀 Funcionalidades
* **🕵️ Discovery Automático:** Varre a rede local para identificar todos os dispositivos conectados.
* **💓 Monitoramento em Tempo Real:** Verifica o status (Ping) de cada dispositivo a cada 3 segundos.
* **📊 Dashboard Web:** Interface limpa que exibe IP, MAC, Hostname e Latência.
* **⚠️ Alertas Visuais:** Linhas da tabela piscam em vermelho instantaneamente se um dispositivo cair.
* **🔌 API REST:** Endpoint JSON (`/api/status`) integrado para consumo de dados externos.

---

## 🛠️ Como Usar

### Pré-requisitos
* Windows (devido ao uso de comandos como `arp -a` e `ping`)
* Python 3.x instalado
* Nenhuma biblioteca externa necessária (apenas Standard Lib)

### Passo a Passo
1.  **Execute o script:**
    ```bash
    python app.py
    ```
2.  **Aguarde o Scan Inicial:** O programa fará uma varredura completa para encontrar os dispositivos.
3.  **Ative o Monitor:** Quando perguntado `Deseja ativar o monitoramento em tempo real? (s/n)`, digite **`s`**.
4.  **Acesse o Dashboard:** Abra seu navegador em:
    👉 **http://localhost:8000**

---

## 🧠 Engenharia e Performance
Para garantir que o monitoramento contínuo não sobrecarregue a rede ou a máquina host, foram implementadas diversas otimizações:

* **Multithreading Inteligente:** Separação entre Thread de UI (Servidor Web) e Thread de Monitoramento (Pings).
* **Smart Polling:** O sistema ajusta o `timeout` dos pings para 500ms para garantir atualizações rápidas sem "floodar" a rede.
* **Consumo Baixo:** Ocupa menos de 5% de CPU e ~50MB de RAM em operação contínua.

> *Para detalhes técnicos profundos sobre as decisões de arquitetura, consulte o arquivo [OTIMIZACOES.md](./OTIMIZACOES.md) incluído neste repositório.*

---

## ⚖️ Créditos e Licença
Este projeto foi desenvolvido por **João Marcos**, baseado no código original *Network Scanner* de **Gustavo Percoski**.

* **Autor do Fork:** João Marcos - Implementação de Server, API, Frontend Dinâmico e Multithreading.
* **Autor Original:** Gustavo Percoski - Lógica base de scan ARP e Template HTML inicial.
