# 🧪 Como Testar o Monitor em Tempo Real

## 📋 Pré-requisitos
- Python 3.x instalado
- Estar conectado a uma rede (Wi-Fi ou Ethernet)
- Porta 8000 disponível

## 🚀 Passo a Passo

### 1. Execute o Scanner
```bash
cd c:\Users\JM\Projetos\Scanner_Rede_Corporativa
python app.py
```

### 2. Aguarde o Scan Inicial
Você verá mensagens como:
```
Iniciando varredura técnica... Aguarde.
Escaneando rede local... Isto pode levar alguns minutos.
```

### 3. Ative o Monitor
Quando perguntado:
```
Deseja ativar o monitoramento em tempo real? (s/n):
```
Digite: **s**

### 4. Acesse a Interface Web
Você verá:
```
====================================================================
🔴 MONITOR EM TEMPO REAL ATIVO
====================================================================
📊 Monitorando XX dispositivos
⏱️  Intervalo de atualização: 5 segundos
🌐 Acesse: http://localhost:8000
====================================================================

✅ Servidor web rodando. Pressione Ctrl+C para parar.
```

Abra seu navegador e acesse: **http://localhost:8000**

## 🎨 O Que Você Verá

### Interface Web
- ✅ Tabela com todos os dispositivos da rede
- 🟢 Status "Online" em verde para dispositivos respondendo
- 🔴 Status "OFFLINE" em vermelho com animação piscante
- ⏱️ Timestamp da última atualização com indicador "● LIVE"
- 📊 Contadores: Total | Online | Offline

### Atualização Automática
A página se atualiza **automaticamente a cada 3 segundos** sem precisar dar refresh!

### Teste de Dispositivo Offline
1. Desligue um dispositivo da rede (ex: celular)
2. Aguarde 5-10 segundos
3. Veja a linha ficar **vermelha e piscando** na tabela!

## 📡 Testando a API

### No Navegador
Acesse: http://localhost:8000/api/status

Você verá um JSON com:
```json
{
  "dispositivos": [
    {
      "ip": "192.168.1.100",
      "mac": "AA:BB:CC:DD:EE:FF",
      "hostname": "PC-EXEMPLO",
      "status": "OK",
      "latencia": "15ms",
      "online": true,
      "class": "ok"
    }
  ],
  "ultima_atualizacao": "09/01/2026 14:30:45",
  "rede_info": {...},
  "status_global": {}
}
```

### Com PowerShell
```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/status | ConvertTo-Json
```

### Com curl
```bash
curl http://localhost:8000/api/status
```

## 🔧 Problemas Comuns

### Porta 8000 já está em uso
**Erro**: `OSError: [WinError 10048] Only one usage of each socket address...`

**Solução**:
```powershell
# Encontre o processo usando a porta
netstat -ano | findstr :8000

# Encerre o processo (substitua XXXX pelo PID)
taskkill /PID XXXX /F
```

### Tabela não atualiza
1. Verifique se o console mostra `[Monitor] Thread de monitoramento iniciada`
2. Abra o Console do navegador (F12) e veja se há erros
3. Confirme que http://localhost:8000/api/status retorna JSON

### Dispositivos não aparecem
- Aguarde até 10 segundos (5s do intervalo + processamento)
- Verifique se o scan inicial encontrou dispositivos
- Firewall do Windows pode estar bloqueando ICMP

## 📊 Monitorando Performance

### Console do Python
Você verá mensagens:
```
[Monitor] Thread de monitoramento iniciada
```

### Console do Navegador (F12)
```javascript
// Sem erros = funcionando corretamente
// Se ver "Failed to fetch" = servidor parado
```

### Task Manager
- **CPU**: Deve estar entre 3-5%
- **Memória**: ~50-70 MB
- **Rede**: Baixo (apenas pings)

## 🛑 Como Parar

1. No terminal onde o Python está rodando
2. Pressione **Ctrl+C**
3. Você verá:
```
[Monitor] Encerrando servidor...
[Monitor] Thread de monitoramento encerrada
```

## 🎯 Teste Completo - Checklist

- [ ] Scanner executou e encontrou dispositivos
- [ ] Ativou o monitoramento (respondeu "s")
- [ ] Console mostra "MONITOR EM TEMPO REAL ATIVO"
- [ ] Acessou http://localhost:8000 no navegador
- [ ] Viu a tabela de dispositivos
- [ ] Viu o indicador "● LIVE" no timestamp
- [ ] Aguardou 3 segundos e viu a página atualizar sozinha
- [ ] Testou desligar um dispositivo e viu ficar vermelho
- [ ] Acessou /api/status e viu o JSON
- [ ] Parou o servidor com Ctrl+C

## 💡 Dicas Extras

### Múltiplas Abas
Você pode abrir **várias abas/navegadores** apontando para http://localhost:8000 e todos verão os mesmos dados em tempo real!

### Compartilhar na Rede Local
Por padrão, o servidor roda em `0.0.0.0:8000`, então **outros PCs na rede** podem acessar:
```
http://[SEU_IP]:8000
```

Exemplo: Se seu IP é `192.168.1.50`:
```
http://192.168.1.50:8000
```

### DevTools para Debug
Abra F12 no navegador → Aba **Network**:
- Você verá requisições GET para `/api/status` a cada 3 segundos
- Status 200 = funcionando
- Status 404/500 = problema no servidor

### Modo Estático vs Dinâmico
O HTML funciona em **2 modos**:

1. **Modo Estático**: Relatório gerado pelo Python (diagnostico_rede.html)
   - Sem atualização automática
   - Snapshot do momento do scan

2. **Modo Dinâmico**: Interface do monitor (http://localhost:8000)
   - Atualização automática a cada 3s
   - Indicador "● LIVE"
   - Animações de offline

## 🎬 Demo Rápida (30 segundos)

```bash
# 1. Execute
python app.py

# 2. Aguarde o scan (1-2 min)
# 3. Digite "s" quando perguntado
# 4. Abra http://localhost:8000
# 5. Aguarde 3 segundos e veja atualizar!
```

## 📝 Logs Esperados

### Console Python (Normal)
```
Iniciando varredura técnica... Aguarde.
Escaneando rede local... Isto pode levar alguns minutos.
Relatório gerado com sucesso!

====================================================================
📊 SCAN COMPLETO!
Dispositivos encontrados: 15
====================================================================

Deseja ativar o monitoramento em tempo real? (s/n): s

====================================================================
🔴 MONITOR EM TEMPO REAL ATIVO
====================================================================
📊 Monitorando 15 dispositivos
⏱️  Intervalo de atualização: 5 segundos
🌐 Acesse: http://localhost:8000
====================================================================

[Monitor] Thread de monitoramento iniciada
✅ Servidor web rodando. Pressione Ctrl+C para parar.
```

### Console Python (Com Problemas)
```
[Monitor] Erro ao verificar dispositivo: [WinError 10060] A connection attempt failed...
# Esse erro pode aparecer ocasionalmente se um dispositivo não responder a tempo
# É NORMAL e não afeta o funcionamento geral
```

---

**✅ Teste concluído com sucesso se você viu todos os itens do checklist!**
