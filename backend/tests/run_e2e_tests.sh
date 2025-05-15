#!/bin/bash
# Script pour exécuter les tests end-to-end

# Définir les couleurs pour une meilleure lisibilité
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}==================================================${NC}"
echo -e "${YELLOW}      EXÉCUTION DES TESTS END-TO-END              ${NC}"
echo -e "${YELLOW}==================================================${NC}"

# Activer l'environnement poetry
echo -e "${YELLOW}Activation de l'environnement Poetry...${NC}"
cd /workspaces/Skyent-dev/backend

# Exécuter les tests de fonctionnalités E2E
echo -e "\n${YELLOW}Exécution des tests de flux E2E...${NC}"
poetry run pytest tests/test_e2e_api.py -v

# Exécuter les tests de gestion des erreurs
echo -e "\n${YELLOW}Exécution des tests de gestion des erreurs...${NC}"
poetry run pytest tests/test_e2e_error_handling.py -v

# Exécuter les tests de performance
echo -e "\n${YELLOW}Exécution des tests de performance...${NC}"
poetry run pytest tests/test_e2e_performance.py -v

echo -e "\n${GREEN}Tests End-to-End terminés !${NC}"
