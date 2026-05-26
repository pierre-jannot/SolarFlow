import nbformat
import subprocess
import asyncio
import sys
import os

nb_path = '../notebooks/modelisation.ipynb'

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

for cell in nb.cells:
    if cell.cell_type == 'code':
        cell.source = cell.source.replace("'time'", "'timestamp'")
        
with open(nb_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Exécution du notebook...")
subprocess.run(['..\\\\.venv\\\\Scripts\\\\python.exe', '-m', 'jupyter', 'nbconvert', '--to', 'notebook', '--execute', '--inplace', nb_path], check=True)

from convert_to_pdf import convert_to_pdf

out_pdf = '../notebooks/modelisation.pdf'
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
asyncio.run(convert_to_pdf(nb_path, out_pdf))
print(f"Terminé : {out_pdf}")
