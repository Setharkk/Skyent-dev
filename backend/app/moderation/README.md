# Module de Modération de Contenu

Ce module fournit des fonctionnalités pour la modération automatique de contenu textuel à travers différentes méthodes et APIs.

## Caractéristiques

- Détection de contenu toxique, inapproprié ou offensant
- Prise en charge de plusieurs fournisseurs:
  - OpenAI Moderation API
  - Anthropic Claude (via prompt spécifique)
  - Detoxify (modèle local)
  - Mode combiné (utilisant plusieurs méthodes)
- API REST pour l'intégration facile
- Analyse par lots de contenus multiples
- Normalisation des résultats entre les différents fournisseurs

## Installation

Le module est intégré au backend et ne nécessite pas d'installation séparée. Cependant, assurez-vous que toutes les dépendances sont installées :

```bash
poetry add openai anthropic detoxify python-dotenv
```

## Configuration

Ajoutez vos clés API dans le fichier `.env` à la racine du projet backend :

```
OPENAI_API_KEY=votre_clé_api_openai
ANTHROPIC_API_KEY=votre_clé_api_anthropic
```

## Utilisation via l'API REST

### Points d'entrée disponibles

- `GET /moderation` - Vérifier le statut du service
- `POST /moderation/moderate` - Endpoint principal avec configuration complète
- `POST /moderation/moderate/text` - Endpoint simplifié pour la modération de texte
- `POST /moderation/moderate/batch` - Modérer une liste de textes en une seule requête

### Exemples d'utilisation

#### Modération simple de texte

```python
import requests

response = requests.post(
    "http://localhost:8000/moderation/moderate/text",
    params={
        "content": "Votre texte à modérer",
        "moderation_type": "openai"  # ou "anthropic", "detoxify", "combined"
    }
)

result = response.json()
print(f"Contenu flaggé: {result['flagged']}")
print(f"Catégories: {result['categories']}")
```

#### Modération avec configuration complète

```python
import requests

data = {
    "content": "Votre texte à modérer",
    "content_type": "text",
    "moderation_type": "combined",
    "include_original_response": True
}

response = requests.post("http://localhost:8000/moderation/moderate", json=data)
result = response.json()
```

#### Modération par lots

```python
import requests

texts = [
    "Premier texte à analyser",
    "Deuxième texte à analyser",
    "Troisième texte à analyser"
]

response = requests.post(
    "http://localhost:8000/moderation/moderate/batch",
    json=texts,
    params={"moderation_type": "detoxify"}
)

results = response.json()
for i, result in enumerate(results):
    print(f"Texte {i+1}: {'Flaggé' if result['flagged'] else 'OK'}")
```

## Utilisation programmatique (dans le code)

Vous pouvez également utiliser directement le service de modération dans votre code Python :

```python
from app.moderation.service import moderation_service
from app.moderation.models import ModerationType, ContentType

async def moderate_user_content(content):
    result = await moderation_service.moderate_content(
        content=content,
        moderation_type=ModerationType.COMBINED,
        content_type=ContentType.TEXT
    )
    
    if result.flagged:
        print("Contenu inapproprié détecté !")
        print(f"Catégories: {result.categories}")
    else:
        print("Contenu approuvé")
    
    return result
```

## Catégories de toxicité détectées

- **Hate** - Discours haineux ou discriminatoire
- **Harassment** - Harcèlement ou intimidation
- **Self_harm** - Contenu lié à l'automutilation ou au suicide
- **Sexual** - Contenu sexuellement explicite
- **Violence** - Descriptions ou menaces de violence
- **Profanity** - Langage grossier ou offensant

## Personnalisation et extension

Le module est conçu pour être facilement extensible. Vous pouvez :

1. Ajouter de nouveaux fournisseurs en implémentant l'interface `ModerationProvider`
2. Ajuster les seuils de détection pour Detoxify dans le code
3. Modifier la logique de combinaison des résultats multiples

## Limitations actuelles

- Seule la modération de texte est prise en charge (pas d'images, audio ou vidéo)
- Les résultats peuvent varier entre les fournisseurs
- Le modèle Detoxify est principalement efficace en anglais
