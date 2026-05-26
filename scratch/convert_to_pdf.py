import asyncio
import sys
import os
from nbconvert import WebPDFExporter
import nbformat

async def convert_to_pdf(nb_path, pdf_path):
    # Forcer l'utilisation de ProactorEventLoop sur Windows (fix NotImplementedError)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    print(f"Chargement du notebook : {nb_path}")
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    
    print("Initialisation de l'exportateur WebPDF...")
    exporter = WebPDFExporter()
    
    print("Conversion en cours (lancement de Chromium)...")
    try:
        output, resources = exporter.from_notebook_node(nb)
        
        print(f"Sauvegarde du PDF : {pdf_path}")
        with open(pdf_path, 'wb') as f:
            f.write(output)
        print("Succès !")
    except Exception as e:
        print(f"Erreur lors de la conversion : {e}")

if __name__ == "__main__":
    tasks = [
        ("notebooks/exploration.ipynb", "notebooks/exploration.pdf"),
        ("notebooks/boxplots_horaires.ipynb", "notebooks/boxplots_horaires.pdf")
    ]
    
    for nb_file, out_pdf in tasks:
        os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
        asyncio.run(convert_to_pdf(nb_file, out_pdf))
