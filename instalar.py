
#!/usr/bin/env python3
import os
import subprocess
import sys

def run_command(command, description=""):
    """Executa um comando e mostra o resultado"""
    if description:
        print(f"🔧 {description}...")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {e}")
        if e.stderr:
            print(f"Detalhes: {e.stderr}")
        return False

def main():
    print("🚀 INICIANDO INSTALAÇÃO DO BOT JINOCA...")
    
    # Atualizar sistema
    if not run_command("apt update && apt upgrade -y", "Atualizando sistema"):
        print("⚠️  Continuando mesmo com erro...")
    
    # Instalar dependências do sistema
    dependencies = [
        "python3",
        "python3-pip", 
        "python3-venv",
        "git",
        "curl",
        "wget"
    ]
    
    for dep in dependencies:
        run_command(f"apt install -y {dep}", f"Instalando {dep}")
    
    # Instalar dependências Python
    python_packages = [
        "flask",
        "requests",
        "qrcode",
        "pillow",
        "pywhatkit",
        "selenium",
        "webdriver-manager"
    ]
    
    print("📦 Instalando dependências Python...")
    for package in python_packages:
        run_command(f"pip3 install {package}", f"Instalando {package}")
    
    # Criar serviço systemd
    service_content = """[Unit]
Description=Bot WhatsApp Jinoca
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/jinoca-bot
ExecStart=/usr/bin/python3 /root/jinoca-bot/jinoca_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open("/etc/systemd/system/jinoca-bot.service", "w") as f:
        f.write(service_content)
    
    # Recarregar e iniciar serviço
    run_command("systemctl daemon-reload", "Configurando serviço automático")
    run_command("systemctl enable jinoca-bot.service", "Ativando inicialização automática")
    
    print("✅ INSTALAÇÃO CONCLUÍDA!")
    print("📱 Para iniciar o bot: python3 jinoca_bot.py")
    print("🌐 Acesse: http://142.93.190.157:3000")

if __name__ == "__main__":
    main()