# 🚀 Fast Ollama LXC Setup

Automatická instalace **Ollama** do LXC kontejneru v Proxmoxu - optimalizováno pro českou a slovenskou komunitu Home Assistant.

---

## ⚡ Quick Start

Spusť tento příkaz v **Proxmox Shell** (jako root):
```bash
curl -sL https://raw.githubusercontent.com/MiregSan/czsk-ai-pro-ha/main/scripts/ollama-lxc-install-script | bash
```

**To je vše!** ☕ Skript zabere ~5-10 minut.

---

## 📋 Co skript dělá?

1. ✅ Automaticky najde volné Container ID (100-999)
2. ✅ Automaticky detekuje správné úložiště
3. ✅ Vytvoří LXC kontejner s Debian 12
4. ✅ Nainstaluje Ollama
5. ✅ Stáhne model **llama3.1:8b** (~4.7GB)
6. ✅ Nakonfiguruje pro vzdálený přístup (API na portu 11434)

---

## 🖥️ Požadavky

- **Proxmox VE** 7.x nebo 8.x
- **8GB RAM** minimálně (doporučeno 16GB)
- **20GB volného místa** na disku
- **Root přístup** do Proxmoxu

---

## 📊 Specifikace kontejneru

| Parametr | Hodnota |
|----------|---------|
| **RAM** | 8GB |
| **Swap** | 2GB |
| **CPU** | 4 cores |
| **Disk** | 20GB |
| **OS** | Debian 12 |
| **Network** | DHCP (bridge vmbr0) |
| **Start on boot** | Ano |

---

## 🎯 Po instalaci

### 1️⃣ Připoj se do kontejneru

**Z Proxmox shellu:**
```bash
pct enter <CTID>
```

**Nebo přes SSH:**
```bash
ssh root@<IP_ADRESA>
# Heslo: ollama123
```

---

### 2️⃣ Spusť chatovací session
```bash
ollama run llama3.1:8b
```

**Příklad použití:**
```
>>> Ahoj, jak se máš?
>>> Napiš mi bash script pro zálohu MySQL databáze
>>> /bye  # Ukončí chat
```

---

### 3️⃣ Použij Ollama API

Ollama je přístupná na portu **11434** přes HTTP API.

**Testovací request:**
```bash
curl http://<IP_ADRESA>:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

**Home Assistant integrace:**
- URL: `http://<IP_ADRESA>:11434`
- Model: `llama3.1:8b`

---

## 🔧 Správa modelů

### Zobrazit nainstalované modely
```bash
ollama list
```

### Stáhnout jiný model
```bash
# Rychlý a lehký (3B parametrů, ~2GB RAM)
ollama pull llama3.2:3b

# Menší verze (1B parametrů, ~1GB RAM)
ollama pull llama3.2:1b

# Alternativa pro kódování
ollama pull qwen2.5:7b
```

### Smazat model
```bash
ollama rm llama3.1:8b
```

### Zjistit velikost modelů
```bash
du -sh /usr/share/ollama/.ollama/models/
```

---

## 🛠️ Užitečné příkazy

### Restartovat Ollama service
```bash
systemctl restart ollama
```

### Zkontrolovat status
```bash
systemctl status ollama
```

### Zobrazit logy
```bash
journalctl -u ollama -f
```

### Změnit heslo root
```bash
passwd
```

---

## 🚨 Troubleshooting

### Kontejner nenaběhl
```bash
# Zkontroluj status
pct status <CTID>

# Zapni manuálně
pct start <CTID>

# Podívej se na logy
pct enter <CTID>
journalctl -xe
```

### Ollama neodpovídá na API
```bash
# Zkontroluj jestli běží
pct enter <CTID>
systemctl status ollama

# Restart service
systemctl restart ollama

# Zkontroluj port
netstat -tlnp | grep 11434
```

### Model se nestáhl
```bash
# Zkontroluj internet v kontejneru
pct enter <CTID>
ping -c 3 ollama.com

# Zkus stáhnout znovu
ollama pull llama3.1:8b
```

### Nedostatek RAM
```bash
# Zkontroluj využití
free -h

# Zvětši RAM kontejneru v Proxmoxu
pct set <CTID> --memory 16384
pct stop <CTID>
pct start <CTID>
```

---

## 🔐 Bezpečnost

⚠️ **Výchozí heslo je `ollama123`** - změň ho po instalaci!
```bash
pct enter <CTID>
passwd
```

⚠️ **Ollama běží na všech IP adresách (0.0.0.0:11434)** - pokud je kontejner na internetu, zabezpeč firewallem!

---

## 📚 Další zdroje

- **Ollama dokumentace:** https://ollama.com/docs
- **Ollama models:** https://ollama.com/library
- **Home Assistant Ollama:** https://www.home-assistant.io/integrations/ollama/
- **CZ/SK HA komunita:** [Link na tvůj Discord/Telegram]

---

## 🤝 Přispění

Návrhy na vylepšení? Otevři **Issue** nebo **Pull Request** na GitHubu!

---

## 📄 Licence

MIT License - volně použitelné pro všechny účely.

---

**Vytvořeno s ❤️ pro CZ/SK Home Assistant komunitu**
```

---

## **Kde to umístit v GitHubu:**
```
czsk-ai-pro-ha/
├── scripts/
│   ├── ollama-lxc-install-script      ← Tvůj bash skript
│   └── README.md                       ← Tento návod
└── README.md                           ← Hlavní README projektu
