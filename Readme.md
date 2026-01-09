# 📡 Network Diagnostic Auto-Scanner

![Python](https://img.shields.io/badge/Python-Standard_Lib-3776AB?logo=python&logoColor=white)
![HTML5](https://img.shields.io/badge/Report-HTML5-E34F26?logo=html5&logoColor=white)
![Focus](https://img.shields.io/badge/Focus-Automation-success)

> **Automatize diagnósticos de rede e suporte técnico com um único clique.**

## 💡 O Problema vs. Solução
Em vez de digitar dezenas de comandos no CMD (`ping`, `ipconfig`, `net stat`) durante um atendimento, o técnico executa este **arquivo portátil (.exe)**.
O resultado é um relatório **HTML visual e interativo** gerado em segundos, pronto para análise ou envio via WhatsApp.

---

## 📸 Preview
![Relatório Gerado](./img/preview.png)

---

## 🚀 Funcionalidades Chave
* **🕵️ Scanner Profundo:** Identifica IP, Gateway, DNS e rastreia o **MAC Address do Roteador** via tabela ARP.
* **⚡ Testes de Latência:** Pings automáticos para Gateway e WAN (Google DNS).
* **🌍 Multi-idioma:** Interface alterna instantaneamente entre **PT-BR / EN / ES**.
* **📋 Botão "Copy-to-Support":** Formata os dados técnicos para colar direto no chat de atendimento.
* **🔴 Monitor em Tempo Real:** Acompanhamento contínuo de dispositivos via interface web.
* **📊 API REST:** Endpoint JSON para integração com outras ferramentas.

---

## 🌐 Monitoramento em Tempo Real

### Funcionalidades do Monitor
* ✅ Interface web interativa em http://localhost:8000
* 📊 Atualização automática a cada 3 segundos
* 💚 Status online/offline em tempo real
* ⚡ Medição de latência para cada dispositivo
* 🎯 API REST (`/api/status`) para integração

### Como Usar o Monitor
1. Execute o scanner normalmente
2. Após o scan inicial, escolha **"s"** quando perguntado sobre monitoramento
3. Acesse http://localhost:8000 no navegador
4. Use **Ctrl+C** para encerrar

### Otimizações de Performance
O sistema foi otimizado para não sobrecarregar a máquina ou rede:
* **Intervalo de 5s** entre ciclos de ping (ajustável no código)
* **Máximo 4 threads** simultâneas no monitor (vs 6 no scan inicial)
* **Timeout de 500ms** para pings rápidos
* **Consumo de rede**: ~1.2 MB/hora para 20 dispositivos

### Configurações Ajustáveis
```python
intervalo_ping = 5          # Segundos entre atualizações
max_threads_monitor = 4     # Threads simultâneas
timeout_ping = 500          # Timeout do ping em ms
```

### API REST
**GET /api/status**
```json
{
  "dispositivos": [
    {
      "ip": "192.168.1.100",
      "mac": "AA:BB:CC:DD:EE:FF",
      "hostname": "PC-EXEMPLO",
      "status": "OK",
      "latencia": "15ms",
      "online": true
    }
  ],
  "ultima_atualizacao": "09/01/2026 14:30:45"
}
```

---

## 🧠 Destaques Técnicos (O que aprendi)
Este projeto foi construído **sem dependências externas** (sem `pip install`), garantindo compatibilidade total com qualquer Windows.

* **Python Puro:** Uso avançado de `subprocess` e `socket` para interagir com o Kernel do Windows.
* **Regex (Expressões Regulares):** Tratamento de strings para extrair dados brutos de comandos do sistema.
* **PyInstaller:** Compilação do script + template HTML em um único executável portátil.
* **Front-end Dinâmico:** HTML/CSS injetado pelo Python com Javascript para interatividade.

---

## 🛠️ Como Usar
1.  Baixe o `.exe` na aba **Releases**.
2.  Execute como Administrador.
3.  O relatório abrirá no seu navegador padrão.

---
**Gustavo Percoski**