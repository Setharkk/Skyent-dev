# Module de Génération et Publication de Contenu

Ce module fournit des fonctionnalités pour la génération automatique de contenu textuel et sa publication sur différentes plateformes de médias sociaux.

## Fonctionnalités

### Génération de contenu

- Création de posts LinkedIn professionnels
- Rédaction de tweets attrayants et concis
- Génération d'articles de blog structurés
- Production de divers types de contenus marketing
- Personnalisation du ton, du style et des contraintes
- Prise en charge de plusieurs langues
- Génération de variantes pour A/B testing

### Publication sur les réseaux sociaux

- Publication directe sur LinkedIn, Twitter, Facebook, etc.
- Planification des publications
- Suivi des publications (statut, URL, etc.)
- Publication depuis un contenu pré-généré ou nouveau
- Support pour les médias (images, vidéos)

## Configuration

Ajoutez vos clés API dans le fichier `.env` :

```bash
# Clés API pour l'IA (génération)
OPENAI_API_KEY="votre_clé_api_openai"
ANTHROPIC_API_KEY="votre_clé_api_anthropic"

# Clés API pour les réseaux sociaux (publication)
LINKEDIN_API_KEY="votre_clé_api_linkedin"
TWITTER_API_KEY="votre_clé_api_twitter"
FACEBOOK_API_KEY="votre_clé_api_facebook"
```

## Utilisation via l'API REST

### Génération de contenu

#### Génération standard avec configuration complète

```bash
curl -X POST "http://localhost:8000/generation/content" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "linkedin_post",
    "prompt": "Présentation de notre nouvelle solution d'IA pour l'optimisation des processus RH",
    "keywords": ["IA", "RH", "innovation"],
    "tone": "professional",
    "include_hashtags": true,
    "include_emojis": true,
    "language": "fr"
  }'
```

#### Génération simplifiée de post LinkedIn

```bash
curl -X POST "http://localhost:8000/generation/linkedin" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Présentation de notre nouvelle solution d'IA pour l'optimisation des processus RH",
    "keywords": ["IA", "RH", "innovation"],
    "tone": "professional"
  }'
```

#### Génération de tweet

```bash
curl -X POST "http://localhost:8000/generation/twitter" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Annonce de notre webinaire sur l'IA en RH ce jeudi",
    "include_hashtags": true
  }'
```

### Publication sur les réseaux sociaux

#### Publication d'un contenu pré-généré

```bash
curl -X POST "http://localhost:8000/publication/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "contenu_id_généré_précédemment",
    "platform": "linkedin"
  }'
```

#### Publication directe sur LinkedIn

```bash
curl -X POST "http://localhost:8000/publication/linkedin" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Nous sommes ravis d'annoncer le lancement de notre nouvelle solution d'IA pour l'optimisation des processus RH ! #IA #RH #Innovation"
  }'
```

#### Publication directe sur Twitter

```bash
curl -X POST "http://localhost:8000/publication/twitter" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Webinaire sur l'IA en RH ce jeudi à 14h ! Inscrivez-vous maintenant sur notre site. #IA #RH #Webinaire",
    "media_urls": ["https://exemple.com/image.jpg"]
  }'
```

### Génération et publication en une seule étape

```bash
curl -X POST "http://localhost:8000/publication/generate-and-publish/linkedin" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Annonce du lancement de notre nouvelle plateforme d'IA pour l'automatisation des tâches RH",
    "keywords": ["IA", "RH", "automatisation"],
    "include_hashtags": true
  }'
```

## Utilisation programmatique dans le code Python

### Génération de contenu

```python
from app.generation.service import generation_service
from app.generation.models import GenerationParameters, ContentType, ContentTone

async def générer_post_linkedin():
    params = GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt="Annonce de notre nouveau partenariat avec Microsoft",
        keywords=["partenariat", "Microsoft", "cloud"],
        tone=ContentTone.PROFESSIONAL,
        include_hashtags=True,
        language="fr"
    )
    
    résultat = await generation_service.generate_content(params)
    print(f"Contenu généré: {résultat.content}")
    return résultat
```

### Publication sur les réseaux sociaux

```python
from app.publication.service import publication_service
from app.publication.models import PublicationRequest, SocialMediaPlatform

async def publier_contenu(content_id):
    request = PublicationRequest(
        content_id=content_id,
        platform=SocialMediaPlatform.LINKEDIN
    )
    
    résultat = await publication_service.publish_content(request)
    print(f"Publication réussie: {résultat.platform_post_url}")
    return résultat
```

## Types de contenus disponibles

- `linkedin_post` - Posts professionnels pour LinkedIn
- `twitter_post` - Tweets courts et engageants
- `blog_article` - Articles de blog structurés
- `newsletter` - Contenu pour newsletters par email
- `email` - Emails professionnels
- `product_description` - Descriptions de produits
- `press_release` - Communiqués de presse
- `marketing_copy` - Textes marketing divers
- `social_media_ad` - Annonces pour médias sociaux

## Tonalités disponibles

- `professional` - Ton professionnel et sérieux
- `casual` - Ton décontracté et conversationnel
- `formal` - Ton très formel
- `friendly` - Ton amical et accessible
- `enthusiastic` - Ton enthousiaste et énergique
- `informative` - Ton informatif et éducatif
- `persuasive` - Ton persuasif et convaincant
- `humorous` - Ton humoristique
- `serious` - Ton sérieux et direct
- `authoritative` - Ton d'autorité et d'expertise

## Plateformes de médias sociaux supportées

- `linkedin` - LinkedIn
- `twitter` - Twitter
- `facebook` - Facebook
- `instagram` - Instagram
- `medium` - Medium
- `youtube` - YouTube (descriptions uniquement)

## Limitations actuelles

- Pour les réseaux sociaux, les publications réelles nécessitent des clés API valides
- La modération de contenu est automatiquement appliquée avant publication
- Les publications planifiées sont simulées (pas d'implémentation de file d'attente persistante)
- Le téléchargement direct de médias n'est pas pris en charge (uniquement les URLs)
