# Yeslek

Yeslek est une plateforme web permettant d'envoyer des recharges mobiles internationales rapidement et en toute sécurité.

L'application est construite avec **Python Flask**, déployée avec **Docker** et **Google Cloud Run**, et utilise plusieurs APIs pour les paiements et la délivrance des recharges.

---

# Architecture

Structure du projet :

```
app.py
routes/
services/
models/
templates/
static/
l10n/
migrations/
config.py
Dockerfile
cloudbuild.yaml
requirements.txt
```

Architecture principale :

* **routes/** → endpoints Flask
* **services/** → logique métier
* **models/** → modèles base de données
* **templates/** → interface Jinja2
* **static/** → CSS, JS, images
* **l10n/** → traductions JSON
* **migrations/** → migrations Alembic

---

# Stack technique

Backend

* Python
* Flask
* SQLAlchemy
* Alembic

Infrastructure

* Docker
* Google Cloud Run
* Google Cloud Build

Paiement et APIs

* Stripe
* Reloadly
* Amazon SES
* Telnyx

Cache / messaging

* Redis

---

# Fonctionnalités

* Recharge mobile internationale
* Paiement sécurisé (Stripe)
* Authentification OTP (SMS / Email)
* Gestion des comptes utilisateurs
* Historique des transactions
* Support multi-langue (FR / EN)

---

# Installation locale

Créer l'environnement :

```bash
python -m venv .venv
```

Activer l'environnement :

Windows

```bash
.venv\Scripts\activate
```

Linux / Mac

```bash
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Lancer l'application :

```bash
python app.py
```

Application disponible sur :

```
http://localhost:8080
```

---

# Variables d'environnement

Créer un fichier `.env` :

```
SECRET_KEY=

DATABASE_URL=

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
SES_FROM_EMAIL=

STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=

RELOADLY_CLIENT_ID=
RELOADLY_CLIENT_SECRET=

TELNYX_API_KEY=
TELNYX_SMS_FROM=
```

---

# Déploiement

Le déploiement est automatisé avec :

* Docker
* Google Cloud Build
* Google Cloud Run

Chaque push sur GitHub déclenche automatiquement :

1. build Docker
2. push image container
3. déploiement Cloud Run

---

# Sécurité

* idempotency pour les recharges
* variables d'environnement sécurisées
* aucune donnée sensible dans le code
* gestion sécurisée des sessions

---

# Licence

Projet privé.
