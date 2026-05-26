import nbformat as nbf

# Chemin du notebook
nb_path = 'notebooks/exploration.ipynb'

# Lecture
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

# Nouvelle cellule d'install (en haut)
install_cell = nbf.v4.new_code_cell("!pip install -q scipy seaborn")
install_cell.metadata = {"tags": ["hide-cell"]}

# Insertion en 2ème position (après l'intro)
nb.cells.insert(1, install_cell)

# Sauvegarde
with open(nb_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Cellule d'installation ajoutée au début du notebook.")
