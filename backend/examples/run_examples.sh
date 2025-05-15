#!/bin/bash
# run_examples.sh
# Script pour exécuter les exemples de génération et publication

cd /workspaces/Skyent-dev/backend

echo "Configuration de l'environnement..."
# Assurez-vous que Poetry est utilisé
poetry shell << EOF

echo "==================================================="
echo "EXEMPLE 1: Génération et publication de contenu"
echo "==================================================="
python examples/generate_and_publish.py

echo -e "\n\n"
echo "==================================================="
echo "EXEMPLE 2: Génération avec modération de contenu"
echo "==================================================="
python examples/generate_with_moderation.py

echo -e "\n\n"
echo "==================================================="
echo "EXEMPLE 3: Génération de posts LinkedIn"
echo "==================================================="
python examples/linkedin_posts.py

# Sortir de Poetry shell
EOF

echo "Tous les exemples ont été exécutés."
