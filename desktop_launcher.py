"""
MOVMASSA WebGIS - Iniciador Desktop Executável
Inicia o servidor local e abre automaticamente a interface no navegador padrão.
"""
import sys
import os
import time
import threading
import webbrowser

# Configuração de caminhos base
if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    APP_DIR = os.path.join(BASE_DIR, 'app_webgis')
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = os.path.join(BASE_DIR, 'app_webgis')

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Importa a aplicação Flask
from app_webgis.app import app

def launch_browser(url, delay=1.5):
    """Aguarda o servidor subir e abre o navegador padrão automaticamente."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[!] Não foi possível abrir o navegador automaticamente: {e}")

def background_sync_on_startup():
    time.sleep(3)
    try:
        from app_webgis.app import sync_with_cloud
        print(" [*] Verificando sincronização com a Nuvem (Render)...")
        ok, msg = sync_with_cloud()
        if ok:
            print(f" [✓] {msg}")
        else:
            print(f" [i] Sincronização em nuvem: {msg}")
    except Exception as e:
        print(f" [i] Modo offline ativo ({e})")

def main():
    port = int(os.environ.get('PORT', 5000))
    url = f"http://127.0.0.1:{port}"

    print("=" * 72)
    print("        SISTEMA WEBGIS MOVMASSA - ANGRA DOS REIS (RJ)")
    print("=" * 72)
    print(f" [✓] Servidor local iniciado em: {url}")
    print(" [✓] Abrindo o seu navegador padrão automaticamente...")
    print(" [i] Para encerrar a aplicação: feche esta janela ou pressione Ctrl+C.")
    print("=" * 72)

    # Inicia abertura do navegador e sincronização em segundo plano
    threading.Thread(target=launch_browser, args=(url,), daemon=True).start()
    threading.Thread(target=background_sync_on_startup, daemon=True).start()

    # Inicia o servidor Flask
    try:
        app.run(host='127.0.0.1', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n[✓] Aplicação encerrada com sucesso.")

if __name__ == '__main__':
    main()
