# Exemples d'utilisation des modules de génération et publication

Ce répertoire contient des exemples d'utilisation des modules de génération de contenu et de publication sur les réseaux sociaux de l'application Skyent.

## Scripts disponibles

1. **`generate_and_publish.py`** - Montre comment générer du contenu et le publier sur LinkedIn et Twitter
2. **`generate_with_moderation.py`** - Illustre l'intégration de la modération de contenu avec la génération
3. **`linkedin_posts.py`** - Exemples spécifiques de génération de différents types de posts LinkedIn
4. **`run_examples.sh`** - Script shell pour exécuter tous les exemples en séquence

## Prérequis

Pour exécuter ces exemples, vous devez :

1. Avoir configuré correctement le fichier `.env` à la racine du backend avec vos clés API
2. Avoir installé toutes les dépendances via Poetry

## Configuration

Assurez-vous que votre fichier `.env` contient les clés API nécessaires :

```
# Clés API pour l'IA (génération)
OPENAI_API_KEY="votre_clé_api_openai"
ANTHROPIC_API_KEY="votre_clé_api_anthropic"

# Clés API pour les réseaux sociaux (publication)
LINKEDIN_API_KEY="votre_clé_api_linkedin"
TWITTER_API_KEY="votre_clé_api_twitter"
FACEBOOK_API_KEY="votre_clé_api_facebook"
```

## Exécution des exemples

Vous pouvez exécuter les exemples individuellement avec Poetry :

```bash
cd /workspaces/Skyent-dev/backend
poetry run python examples/linkedin_posts.py
```

Ou exécuter tous les exemples en séquence avec le script shell :

```bash
cd /workspaces/Skyent-dev/backend
./examples/run_examples.sh
```

## Notes importantes

- Les scripts fonctionnent même sans clés API, mais les fonctionnalités de publication réelle seront simulées
- La génération de contenu utilise l'API d'OpenAI ou Anthropic, donc ces clés sont nécessaires pour la génération réelle
- Pour la publication réelle sur les réseaux sociaux, vous devez configurer les clés API correspondantes

## Personnalisation

Vous pouvez modifier ces exemples pour :

1. Utiliser différents types de contenu (voir `ContentType` dans `app/generation/models.py`)
2. Expérimenter avec différentes tonalités (voir `ContentTone` dans `app/generation/models.py`)
3. Publier sur d'autres plateformes (voir `SocialMediaPlatform` dans `app/publication/models.py`)
