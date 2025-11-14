
#!/usr/bin/env python3
import os
import subprocess
import sys

def run_command(command, description=""):
    if description:
        print(f"🔧 {description}...")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🚀 INSTALANDO BOT JINOCA...")
    
    # Atualizar sistema
    run_command("apt update && apt upgrade -y", "Atualizando sistema")
    
    # Instalar Python e dependências
    run_command("apt install -y python3 python3-pip", "Instalando Python")
    
    # Instalar dependências Python
    packages = [
        "flask",
        "requests", 
        "qrcode",
        "pillow",
        "pywhatkit"
    ]
    
    for package in packages:
        run_command(f"pip3 install {package}", f"Instalando {package}")
    
    print("✅ INSTALAÇÃO CONCLUÍDA!")
    print("📱 Para iniciar: python3 jinoca_bot.py")
    print("🌐 Acesse: http://142.93.190.157:3000")

if __name__ == "__main__":
    main()