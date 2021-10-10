# PointingInterface

Interface pour pointer à la main des détails sur des images.

Les images sont chargées en mémoire une par une afin de ne pas avoir de limitation sur le nombre d'images à traiter.

Utilise la librairie [pyqtgraph](https://www.pyqtgraph.org/).

## Utilisation :

Le chemin des images ainsi que la liste des détails à pointer doivent être précisés dans le fichier PointingInterface_main.py

    # names and colors of the points
    points=[
        ['Point 1', [255,255,0]],
        ['Point 2', [0,255,255]],
        ]
    # path of the images
    path='.\\example\\*.jpg'

Les coordonnées des points et les noms des images associées sont enregistrés dans des fichiers .npy