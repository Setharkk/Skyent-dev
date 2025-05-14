# Skyent-dev

Monorepo pour le projet Skyent-dev, comprenant un backend Python (FastAPI) et un frontend React (TypeScript).

## Structure du projet

- `backend/`: Application backend en Python, gérée avec Poetry.
- `docs/`: Documentation du projet, y compris les diagrammes d'architecture et les décisions de conception.
- `frontend/`: Application frontend en React/TypeScript, gérée avec pnpm et Vite.
- `Makefile`: Scripts pour faciliter les tâches courantes (installation, build, etc.).
- `.instructions.md`: Conventions de codage et de développement pour Xenolab.

## Prérequis

- [Python 3.12+](https://www.python.org/)
- [Poetry](https://python-poetry.org/) (pour le backend)
- [Node.js](https://nodejs.org/) (avec npm/pnpm) (pour le frontend)
- [pnpm 8+](https://pnpm.io/)
- [Make](https://www.gnu.org/software/make/)

## Installation

Pour installer toutes les dépendances du projet (backend et frontend), exécutez la commande suivante à la racine du projet :

```bash
make setup
```

Cela installera les dépendances Python à l'aide de Poetry et les dépendances Node.js à l'aide de pnpm.

## Développement

Consultez les README spécifiques dans les dossiers `backend/` et `frontend/` pour plus d'informations sur le lancement des serveurs de développement et les autres scripts disponibles.

## Conventions

Veuillez consulter le fichier `.instructions.md` pour les conventions de codage, de nommage et de commit à suivre pour ce projet.