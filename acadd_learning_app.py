import os
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, Response, flash, redirect, render_template_string, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'acadd_learning_secret_key_2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acadd_learning_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False, unique=True)
    entreprise = db.Column(db.String(120), nullable=True)
    niveau = db.Column(db.String(50), nullable=False, default='Débutant')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    inscriptions = db.relationship('Enrollment', backref='user', lazy=True)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(180), nullable=False)
    categorie = db.Column(db.String(80), nullable=False)
    niveau = db.Column(db.String(50), nullable=False)
    duree_jours = db.Column(db.Integer, nullable=False)
    public_cible = db.Column(db.String(120), nullable=True)
    modalite = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    prix = db.Column(db.Float, default=0.0)
    statut = db.Column(db.String(50), default='À venir')
    formateur_nom = db.Column(db.String(120), nullable=True)
    formateur_email = db.Column(db.String(120), nullable=True)
    validation_status = db.Column(db.String(50), nullable=False, default='Approuvée')
    live_date = db.Column(db.String(20), nullable=True)
    live_time = db.Column(db.String(10), nullable=True)
    live_url = db.Column(db.String(500), nullable=True)
    steps = db.relationship('CourseStep', backref='course', lazy=True, cascade='all, delete-orphan')
    inscriptions = db.relationship('Enrollment', backref='course', lazy=True)


class CourseStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    ordre = db.Column(db.Integer, nullable=False)
    titre = db.Column(db.String(180), nullable=False)
    duree_min = db.Column(db.Integer, nullable=False)
    type_module = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.Column(db.Integer, default=0)
    statut = db.Column(db.String(50), default='En cours')


class PaymentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    reference = db.Column(db.String(120), nullable=False)
    telephone_payeur = db.Column(db.String(30), nullable=False)
    montant = db.Column(db.Integer, nullable=False)
    statut = db.Column(db.String(50), nullable=False, default='À vérifier')
    date_demande = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='paiements')
    course = db.relationship('Course', backref='paiements')


HTML_BASE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ACADD Learning</title>
    <meta name="description" content="ACADD Learning : formations en ligne au Sénégal, cours numériques, espace apprenant et formations proposées par des formateurs.">
    <meta name="keywords" content="ACADD Learning, formations en ligne Sénégal, cours numériques, formation professionnelle, apprentissage en ligne">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{{ request.url }}">
    <meta property="og:type" content="website">
    <meta property="og:title" content="ACADD Learning - Formations en ligne">
    <meta property="og:description" content="Découvrez les formations numériques et développez vos compétences avec ACADD Learning.">
    <meta property="og:url" content="{{ request.url }}">
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "EducationalOrganization",
      "name": "ACADD Learning",
      "url": "{{ request.url_root }}",
      "description": "Plateforme de formations en ligne et de cours numériques au Sénégal."
    }
    </script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body { background: linear-gradient(180deg, #f4f8ff 0%, #eef3ff 100%); }
        .navbar { background: linear-gradient(90deg, #101d5d, #1d4ed8); }
        .hero { background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(29, 78, 216, 0.90)); color: white; border-radius: 24px; }
        .course-card { border: none; border-radius: 18px; box-shadow: 0 12px 30px rgba(30,41,59,0.08); transition: transform 0.2s ease; }
        .course-card:hover { transform: translateY(-3px); }
        .badge-acadd { background: #dbeafe; color: #1d4ed8; }
        .progress { height: 12px; }
        .btn-acadd { background: #1d4ed8; border-color: #1d4ed8; }
        .btn-acadd:hover { background: #1e40af; border-color: #1e40af; }
        .icon-box { width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; background: #edf2ff; color: #1d4ed8; font-size: 1.4rem; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark shadow-sm">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">ACADD Learning</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Catalogue</a>
                <a class="nav-link" href="/dashboard">Mon espace</a>
                <a class="nav-link" href="/profil">Profil</a>
                <a class="nav-link" href="/formateur">Espace formateur</a>
                <a class="nav-link" href="/admin">Validation ACADD</a>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {{ body_content | safe }}
    </div>
</body>
</html>
"""

HTML_HOME = """
<section class="hero p-4 p-lg-5 mb-4">
    <div class="row align-items-center">
        <div class="col-lg-7">
            <span class="badge badge-acadd px-3 py-2 mb-3">ACADD • Formation en ligne</span>
            <h1 class="display-6 fw-bold mb-3">Apprends le numérique, l’IA et le web à ton rythme</h1>
            <p class="lead text-white-50 mb-4">
                Suis des formations pratiques, certifiantes et accessibles en ligne, avec suivi de progression et accompagnement personnalisé.
            </p>
            <p class="mb-4 fw-semibold">Tarifs adaptés au niveau : de 15 000 à 90 000 FCFA.</p>
            <div class="d-flex gap-3 flex-wrap">
                <a href="#catalogue" class="btn btn-light btn-lg">Découvrir les formations</a>
                <a href="/dashboard" class="btn btn-outline-light btn-lg">Voir mon parcours</a>
            </div>
        </div>
        <div class="col-lg-5 mt-4 mt-lg-0">
            <div class="bg-white text-dark rounded-4 p-4 shadow">
                <h5 class="fw-bold mb-3">Bienvenue {{ user_name }}</h5>
                <form method="POST" action="/profil">
                    <div class="mb-3">
                        <label class="form-label">Votre nom</label>
                        <input type="text" name="nom" class="form-control" value="{{ user_name }}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Votre structure</label>
                        <input type="text" name="entreprise" class="form-control" placeholder="Orange Digital Center, ACADD, ..." value="{{ entreprise }}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Votre niveau</label>
                        <select name="niveau" class="form-select" required>
                            {% for level in levels %}
                            <option value="{{ level }}" {% if niveau == level %}selected{% endif %}>{{ level }}</option>
                            {% endfor %}
                        </select>
                        <div class="form-text">Ce choix nous aide à vous orienter vers les formations adaptées.</div>
                    </div>
                    <button type="submit" class="btn btn-acadd w-100">Enregistrer le profil</button>
                </form>
            </div>
        </div>
    </div>
</section>

<div class="row g-3 mb-4">
    <div class="col-md-3">
        <div class="card border-0 shadow-sm rounded-4 h-100">
            <div class="card-body d-flex align-items-center gap-3">
                <div class="icon-box">📘</div>
                <div>
                    <div class="text-muted small">Formations</div>
                    <div class="fs-4 fw-bold">{{ total_courses }}</div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-0 shadow-sm rounded-4 h-100">
            <div class="card-body d-flex align-items-center gap-3">
                <div class="icon-box">🎯</div>
                <div>
                    <div class="text-muted small">Inscrits</div>
                    <div class="fs-4 fw-bold">{{ total_enrollments }}</div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-0 shadow-sm rounded-4 h-100">
            <div class="card-body d-flex align-items-center gap-3">
                <div class="icon-box">📈</div>
                <div>
                    <div class="text-muted small">Progression moyenne</div>
                    <div class="fs-4 fw-bold">{{ avg_progress }}%</div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-0 shadow-sm rounded-4 h-100">
            <div class="card-body d-flex align-items-center gap-3">
                <div class="icon-box">✅</div>
                <div>
                    <div class="text-muted small">Terminé</div>
                    <div class="fs-4 fw-bold">{{ completed_courses }}</div>
                </div>
            </div>
        </div>
    </div>
</div>

<div id="catalogue" class="mb-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2 class="fw-bold mb-0">Catalogue des formations</h2>
    </div>
    <div class="row g-4">
        {% for course in courses %}
        <div class="col-lg-4 col-md-6">
            <div class="card course-card h-100">
                <div class="card-body d-flex flex-column">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <span class="badge bg-primary-subtle text-primary-emphasis rounded-pill px-3 py-2">{{ course.categorie }}</span>
                        <span class="text-muted small">{{ course.duree_jours }} jours</span>
                    </div>
                    <h4 class="fw-bold mb-2">{{ course.titre }}</h4>
                    <p class="text-muted small mb-3">{{ course.description }}</p>
                    <ul class="list-inline small text-muted mb-3">
                        <li class="list-inline-item">Niveau: <strong>{{ course.niveau }}</strong></li>
                        <li class="list-inline-item">•</li>
                        <li class="list-inline-item">Public: {{ course.public_cible }}</li>
                    </ul>
                    <div class="mt-auto">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <span class="fw-bold text-primary">{{ course.modalite }}</span>
                            <span class="fw-bold">{{ "{:,.0f}".format(course.prix).replace(",", " ") }} FCFA</span>
                        </div>
                        <div class="d-grid gap-2 d-md-block">
                            <a href="/cours/{{ course.id }}" class="btn btn-outline-primary">Voir les détails</a>
                            <a href="/inscrire/{{ course.id }}" class="btn btn-acadd">S'inscrire</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
"""

HTML_COURSE_DETAIL = """
<div class="row g-4">
    <div class="col-lg-8">
        <div class="card border-0 shadow-sm rounded-4 mb-4">
            <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-start mb-3 flex-wrap gap-2">
                    <div>
                        <span class="badge bg-primary-subtle text-primary-emphasis px-3 py-2 mb-2">{{ course.categorie }}</span>
                        <h1 class="fw-bold mb-1">{{ course.titre }}</h1>
                    </div>
                    <span class="badge bg-success text-white px-3 py-2">{{ course.statut }}</span>
                </div>
                <p class="lead text-muted">{{ course.description }}</p>

                <div class="row mb-4 g-3">
                    <div class="col-md-3">
                        <div class="bg-light rounded-3 p-3">
                            <small class="text-muted d-block">Durée</small>
                            <strong>{{ course.duree_jours }} jours</strong>
                        </div>
                    </div>
                    {% if course.live_date and course.live_time %}
                    <div class="alert alert-primary">
                        <strong>Cours en direct</strong><br>
                        Date : {{ course.live_date }} à {{ course.live_time }}
                        {% if can_access and course.live_url %}
                        <br><a class="btn btn-acadd btn-sm mt-2" href="{{ course.live_url }}" target="_blank" rel="noopener">Rejoindre le cours en direct</a>
                        {% elif not can_access %}
                        <br><small>Le lien sera disponible après confirmation de votre paiement.</small>
                        {% endif %}
                    </div>
                    {% endif %}
                    <div class="col-md-3">
                        <div class="bg-light rounded-3 p-3">
                            <small class="text-muted d-block">Niveau</small>
                            <strong>{{ course.niveau }}</strong>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="bg-light rounded-3 p-3">
                            <small class="text-muted d-block">Modalité</small>
                            <strong>{{ course.modalite }}</strong>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="bg-light rounded-3 p-3">
                            <small class="text-muted d-block">Prix</small>
                            <strong>{{ "{:,.0f}".format(course.prix).replace(",", " ") }} FCFA</strong>
                        </div>
                    </div>
                </div>

                <h3 class="fw-bold mb-3">Programme du cours</h3>
                <div class="list-group">
                    {% for step in course.steps %}
                    <div class="list-group-item border-0 rounded-3 mb-2 shadow-sm">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <div class="fw-bold">Module {{ step.ordre }} : {{ step.titre }}</div>
                                <small class="text-muted">{{ step.type_module }} • {{ step.duree_min }} min</small>
                            </div>
                            <span class="badge bg-light text-dark">{{ step.type_module }}</span>
                        </div>
                        {% if step.description %}
                        <p class="mb-0 mt-2 text-muted small">{{ step.description }}</p>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <div class="col-lg-4">
        <div class="card border-0 shadow-sm rounded-4 p-3 sticky-top" style="top: 20px;">
            <h4 class="fw-bold mb-3">Enregistrer mon parcours</h4>
            <p class="text-muted">Commencez ce parcours en ligne et suivez votre progression sur votre espace personnel.</p>
            <a href="/inscrire/{{ course.id }}" class="btn btn-acadd w-100 mb-2">Payer et s'inscrire</a>
            <a href="/" class="btn btn-outline-secondary w-100">Retour au catalogue</a>
        </div>
    </div>
</div>
"""

HTML_DASHBOARD = """
<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
    <div>
        <h2 class="fw-bold mb-1">Mon espace d'apprentissage</h2>
        <p class="text-muted mb-0">Bonjour {{ user_name }}, niveau sélectionné : <strong>{{ niveau }}</strong>.</p>
    </div>
    <a href="/" class="btn btn-acadd">Découvrir d'autres formations</a>
</div>

{% if inscriptions %}
<div class="row g-4">
    {% for enrollment in inscriptions %}
    <div class="col-lg-6">
        <div class="card border-0 shadow-sm rounded-4 h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <span class="badge bg-primary-subtle text-primary-emphasis mb-2">{{ enrollment.course.categorie }}</span>
                        <h4 class="mb-1">{{ enrollment.course.titre }}</h4>
                    </div>
                    <span class="badge bg-success text-white">{{ enrollment.statut }}</span>
                </div>

                <div class="mb-3">
                    <div class="d-flex justify-content-between small text-muted mb-1">
                        <span>Progression</span>
                        <strong>{{ enrollment.progress }}%</strong>
                    </div>
                    <div class="progress">
                        <div class="progress-bar bg-success" role="progressbar" style="width: {{ enrollment.progress }}%"></div>
                    </div>
                </div>

                <form method="POST" action="/progress/{{ enrollment.course.id }}">
                    <label class="form-label small text-muted">Mettre à jour votre progression</label>
                    <div class="input-group">
                        <input type="range" min="0" max="100" value="{{ enrollment.progress }}" name="progress" class="form-range w-100" id="progress-{{ enrollment.id }}">
                        <button type="submit" class="btn btn-acadd">Valider</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="card border-0 shadow-sm rounded-4 p-5 text-center">
    <h4 class="mb-3">Aucune formation suivie pour le moment</h4>
    <p class="text-muted mb-4">Choisissez une formation dans le catalogue pour commencer votre parcours ACADD.</p>
    <a href="/" class="btn btn-acadd">Explorer les formations</a>
</div>
{% endif %}
{% if paiements %}
<div class="card border-0 shadow-sm rounded-4 mt-4">
    <div class="card-body">
        <h4 class="fw-bold">Mes demandes de paiement</h4>
        {% for payment in paiements %}
        <div class="d-flex justify-content-between border-bottom py-2">
            <span>{{ payment.course.titre }} — {{ "{:,.0f}".format(payment.montant).replace(",", " ") }} FCFA</span>
            <strong>{{ payment.statut }}</strong>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}
"""

HTML_PAYMENT = """
<div class="row justify-content-center">
    <div class="col-lg-7">
        <div class="card border-0 shadow-sm rounded-4">
            <div class="card-body p-4">
                <span class="badge bg-primary-subtle text-primary-emphasis mb-2">{{ course.niveau }}</span>
                <h2 class="fw-bold">{{ course.titre }}</h2>
                <p class="text-muted">Montant à payer : <strong>{{ "{:,.0f}".format(course.prix).replace(",", " ") }} FCFA</strong></p>
                <div class="alert alert-info">
                    Transférez exactement ce montant au numéro <strong>77 089 01 47</strong> via votre service Mobile Money.
                    Gardez la référence de transaction : elle sera vérifiée par ACADD.
                </div>
                <form method="POST" action="/paiement/{{ course.id }}">
                    <div class="mb-3"><label class="form-label">Votre numéro de paiement *</label><input name="telephone_payeur" class="form-control" placeholder="Ex : 77 000 00 00" required></div>
                    <div class="mb-3"><label class="form-label">Référence de transaction *</label><input name="reference" class="form-control" placeholder="Référence reçue après le transfert" required><div class="form-text">Après le transfert, copiez l’ID de transaction indiqué dans le SMS ou l’historique Mobile Money, puis collez-le ici.</div></div>
                    <button class="btn btn-acadd w-100">Envoyer la demande de vérification</button>
                </form>
            </div>
        </div>
    </div>
</div>
"""

HTML_FORMATEUR = """
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="card border-0 shadow-sm rounded-4">
            <div class="card-body p-4">
                <h2 class="fw-bold">Proposer une formation</h2>
                <p class="text-muted">Votre formation sera vérifiée par l'équipe ACADD avant d'être publiée.</p>
                <form method="POST">
                    <div class="row g-3">
                        <div class="col-md-6"><label class="form-label">Nom du formateur *</label><input name="formateur_nom" class="form-control" required></div>
                        <div class="col-md-6"><label class="form-label">E-mail *</label><input type="email" name="formateur_email" class="form-control" required></div>
                        <div class="col-md-8"><label class="form-label">Titre de la formation *</label><input name="titre" class="form-control" required></div>
                        <div class="col-md-4"><label class="form-label">Catégorie *</label><input name="categorie" class="form-control" placeholder="IA, Web..." required></div>
                        <div class="col-md-4"><label class="form-label">Niveau *</label><select name="niveau" class="form-select" required><option>Débutant</option><option>Intermédiaire</option><option>Professionnel</option></select></div>
                        <div class="col-md-4"><label class="form-label">Durée (jours) *</label><input type="number" name="duree_jours" min="1" max="365" class="form-control" required></div>
                        <div class="col-md-4"><label class="form-label">Prix (FCFA) *</label><input type="number" name="prix" min="15000" max="90000" step="1000" class="form-control" required></div>
                        <div class="col-md-4"><label class="form-label">Date du direct *</label><input type="date" name="live_date" class="form-control" required></div>
                        <div class="col-md-4"><label class="form-label">Heure du direct *</label><input type="time" name="live_time" class="form-control" required></div>
                        <div class="col-md-8"><label class="form-label">Lien Google Meet, Zoom ou Jitsi *</label><input type="url" name="live_url" class="form-control" placeholder="https://..." required></div>
                        <div class="col-12"><label class="form-label">Description *</label><textarea name="description" rows="5" class="form-control" required></textarea></div>
                    </div>
                    <button class="btn btn-acadd mt-4">Soumettre à ACADD</button>
                </form>
            </div>
        </div>
    </div>
</div>
"""

HTML_ADMIN = """
<div class="d-flex justify-content-between align-items-center mb-4">
    <div><h2 class="fw-bold mb-1">Validation des formations</h2><p class="text-muted mb-0">Les formations ne sont publiques qu'après validation ACADD.</p></div>
    <a href="/formateur" class="btn btn-outline-primary">Espace formateur</a>
</div>
{% if pending %}
<div class="row g-4">
{% for course in pending %}
<div class="col-lg-6"><div class="card border-0 shadow-sm rounded-4 h-100"><div class="card-body">
    <span class="badge bg-warning text-dark mb-2">En attente</span>
    <h4>{{ course.titre }}</h4><p class="text-muted">{{ course.description }}</p>
    <p class="small mb-3"><strong>Formateur :</strong> {{ course.formateur_nom }} ({{ course.formateur_email }})<br><strong>Niveau :</strong> {{ course.niveau }} • <strong>Prix :</strong> {{ "{:,.0f}".format(course.prix).replace(",", " ") }} FCFA</p>
    <form method="POST" action="/admin/formation/{{ course.id }}/valider" class="d-inline"><button class="btn btn-success">Valider et publier</button></form>
    <form method="POST" action="/admin/formation/{{ course.id }}/refuser" class="d-inline"><button class="btn btn-outline-danger">Refuser</button></form>
</div></div></div>
{% endfor %}
</div>
{% else %}<div class="alert alert-success">Aucune formation en attente de validation.</div>{% endif %}
<h3 class="fw-bold mt-5 mb-3">Paiements à vérifier</h3>
{% if payments %}
<div class="table-responsive"><table class="table table-bordered bg-white align-middle"><thead><tr><th>Apprenant</th><th>Formation</th><th>Montant</th><th>Téléphone</th><th>Référence</th><th>Action</th></tr></thead><tbody>
{% for payment in payments %}<tr><td>{{ payment.user.nom }}</td><td>{{ payment.course.titre }}</td><td>{{ "{:,.0f}".format(payment.montant).replace(",", " ") }} FCFA</td><td>{{ payment.telephone_payeur }}</td><td>{{ payment.reference }}</td><td><form method="POST" action="/admin/paiement/{{ payment.id }}/autoriser" class="d-inline"><button class="btn btn-sm btn-success">Autoriser l'accès</button></form> <form method="POST" action="/admin/paiement/{{ payment.id }}/refuser" class="d-inline"><button class="btn btn-sm btn-outline-danger">Refuser</button></form></td></tr>{% endfor %}
</tbody></table></div>
{% else %}<div class="alert alert-secondary">Aucun paiement à vérifier.</div>{% endif %}
"""


@app.route('/')
def index():
    user_name = session.get('user_name', 'Apprenant')
    enterprise = session.get('enterprise', '')
    niveau = session.get('niveau', 'Débutant')
    levels = ['Débutant', 'Intermédiaire', 'Professionnel']
    courses = Course.query.filter_by(validation_status='Approuvée').order_by(Course.id).all()

    total_courses = Course.query.count()
    total_enrollments = Enrollment.query.count()
    avg_progress = 0
    if total_enrollments:
        avg_progress = round(sum(e.progress for e in Enrollment.query.all()) / total_enrollments)
    completed_courses = Enrollment.query.filter(Enrollment.progress >= 100).count()

    content = render_template_string(
        HTML_HOME,
        courses=courses,
        total_courses=total_courses,
        total_enrollments=total_enrollments,
        avg_progress=avg_progress,
        completed_courses=completed_courses,
        user_name=user_name,
        entreprise=enterprise,
        niveau=niveau,
        levels=levels,
    )
    return render_template_string(HTML_BASE, body_content=content)


@app.route('/robots.txt')
def robots():
    sitemap_url = url_for('sitemap', _external=True)
    return Response(
        f'User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /dashboard\nDisallow: /profil\nSitemap: {sitemap_url}\n',
        mimetype='text/plain',
    )


@app.route('/sitemap.xml')
def sitemap():
    pages = [url_for('index', _external=True)]
    pages.extend(
        url_for('course_detail', course_id=course.id, _external=True)
        for course in Course.query.filter_by(validation_status='Approuvée').all()
    )
    urls = ''.join(f'<url><loc>{page}</loc></url>' for page in pages)
    
    

return Response(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        mimetype='application/xml',
    )


@app.route('/google09a461f016322a8f.html')
def google_site_verification():
        return Response('google-site-verification: google09a461f016322a8f.html', mimetype='text/plain')
    

@app.route('/profil', methods=['POST', 'GET'])
def profil():
    if request.method == 'POST':
        nom = (request.form.get('nom') or '').strip()
        entreprise = (request.form.get('entreprise') or '').strip()
        niveau = request.form.get('niveau', 'Débutant')
        levels = {'Débutant', 'Intermédiaire', 'Professionnel'}
        if not nom:
            flash('Le nom est obligatoire pour personnaliser votre parcours.', 'danger')
            return redirect(url_for('index'))
        if niveau not in levels:
            flash('Le niveau sélectionné est invalide.', 'danger')
            return redirect(url_for('index'))
        session['user_name'] = nom
        session['enterprise'] = entreprise
        session['niveau'] = niveau
        user = User.query.filter_by(nom=nom).first()
        if not user:
            user = User(nom=nom, entreprise=entreprise, niveau=niveau)
            db.session.add(user)
        else:
            user.entreprise = entreprise
            user.niveau = niveau
        db.session.commit()
        flash(f'Profil enregistré pour {nom}.', 'success')
        return redirect(url_for('index'))

    user_name = session.get('user_name', 'Apprenant')
    enterprise = session.get('enterprise', '')
    niveau = session.get('niveau', 'Débutant')
    return render_template_string(
        HTML_BASE,
        body_content=f"""
        <div class='card border-0 shadow-sm rounded-4 p-4'>
            <h2 class='fw-bold mb-3'>Mon profil</h2>
            <form method='POST'>
                <div class='mb-3'>
                    <label class='form-label'>Nom</label>
                    <input type='text' class='form-control' name='nom' value='{user_name}' required>
                </div>
                <div class='mb-3'>
                    <label class='form-label'>Entreprise</label>
                    <input type='text' class='form-control' name='entreprise' value='{enterprise}'>
                </div>
                <div class='mb-3'>
                    <label class='form-label'>Niveau</label>
                    <select class='form-select' name='niveau' required>
                        <option value='Débutant' {'selected' if niveau == 'Débutant' else ''}>Débutant</option>
                        <option value='Intermédiaire' {'selected' if niveau == 'Intermédiaire' else ''}>Intermédiaire</option>
                        <option value='Professionnel' {'selected' if niveau == 'Professionnel' else ''}>Professionnel</option>
                    </select>
                </div>
                <button type='submit' class='btn btn-acadd'>Sauvegarder</button>
            </form>
        </div>
        """
    )


@app.route('/cours/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    if course.validation_status != 'Approuvée':
        flash('Cette formation est encore en cours de validation.', 'warning')
        return redirect(url_for('index'))
    user = User.query.filter_by(nom=session.get('user_name', 'Apprenant')).first()
    can_access = bool(user and Enrollment.query.filter_by(
        user_id=user.id, course_id=course.id, statut='Accès autorisé'
    ).first())
    content = render_template_string(HTML_COURSE_DETAIL, course=course, can_access=can_access)
    return render_template_string(HTML_BASE, body_content=content)


@app.route('/inscrire/<int:course_id>')
def inscrire(course_id):
    course = Course.query.get_or_404(course_id)
    if course.validation_status != 'Approuvée':
        flash('Cette formation n’est pas encore disponible.', 'warning')
        return redirect(url_for('index'))
    content = render_template_string(HTML_PAYMENT, course=course)
    return render_template_string(HTML_BASE, body_content=content)


@app.route('/paiement/<int:course_id>', methods=['POST'])
def submit_payment(course_id):
    course = Course.query.get_or_404(course_id)
    user_name = session.get('user_name', 'Apprenant')
    user = User.query.filter_by(nom=user_name).first()
    if not user:
        user = User(
            nom=user_name,
            entreprise=session.get('enterprise', ''),
            niveau=session.get('niveau', 'Débutant'),
        )
        db.session.add(user)
        db.session.commit()

    existing = Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first()
    if existing:
        flash(f'Vous avez déjà accès à la formation "{course.titre}".', 'info')
        return redirect(url_for('dashboard'))

    pending = PaymentRequest.query.filter_by(
        user_id=user.id, course_id=course.id, statut='À vérifier'
    ).first()
    if pending:
        flash('Une demande de paiement est déjà en attente de vérification.', 'info')
        return redirect(url_for('dashboard'))

    reference = (request.form.get('reference') or '').strip()
    telephone_payeur = (request.form.get('telephone_payeur') or '').strip()
    if not reference or not telephone_payeur:
        flash('Le numéro de paiement et la référence sont obligatoires.', 'danger')
        return redirect(url_for('inscrire', course_id=course.id))

    payment = PaymentRequest(
        user_id=user.id,
        course_id=course.id,
        reference=reference,
        telephone_payeur=telephone_payeur,
        montant=int(course.prix),
    )
    db.session.add(payment)
    db.session.commit()
    flash('Demande envoyée. Votre accès sera activé après vérification du paiement.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    user_name = session.get('user_name', 'Apprenant')
    niveau = session.get('niveau', 'Débutant')
    user = User.query.filter_by(nom=user_name).first()
    inscriptions = []
    paiements = []
    if user:
        niveau = user.niveau
        session['niveau'] = niveau
        inscriptions = Enrollment.query.filter_by(user_id=user.id).order_by(Enrollment.date_inscription.desc()).all()
        paiements = PaymentRequest.query.filter_by(user_id=user.id).order_by(PaymentRequest.date_demande.desc()).all()

    content = render_template_string(HTML_DASHBOARD, user_name=user_name, niveau=niveau, inscriptions=inscriptions, paiements=paiements)
    return render_template_string(HTML_BASE, body_content=content)


@app.route('/progress/<int:course_id>', methods=['POST'])
def update_progress(course_id):
    user_name = session.get('user_name', 'Apprenant')
    user = User.query.filter_by(nom=user_name).first()
    if not user:
        flash('Veuillez enregistrer votre profil avant de suivre une formation.', 'warning')
        return redirect(url_for('index'))

    enrollment = Enrollment.query.filter_by(user_id=user.id, course_id=course_id).first()
    if not enrollment:
        flash('Cette formation n’est pas dans votre parcours.', 'danger')
        return redirect(url_for('dashboard'))

    new_progress = max(0, min(100, int(request.form.get('progress', 0))))
    enrollment.progress = new_progress
    enrollment.statut = 'Terminé' if new_progress >= 100 else 'En cours'
    db.session.commit()

    flash(f'Progression mise à jour : {new_progress}%.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/formateur', methods=['GET', 'POST'])
def formateur():
    if request.method == 'POST':
        formateur_nom = (request.form.get('formateur_nom') or '').strip()
        formateur_email = (request.form.get('formateur_email') or '').strip()
        titre = (request.form.get('titre') or '').strip()
        categorie = (request.form.get('categorie') or '').strip()
        niveau = request.form.get('niveau', 'Débutant')
        description = (request.form.get('description') or '').strip()
        live_date = (request.form.get('live_date') or '').strip()
        live_time = (request.form.get('live_time') or '').strip()
        live_url = (request.form.get('live_url') or '').strip()
        try:
            duree_jours = int(request.form.get('duree_jours', '0'))
            prix = int(request.form.get('prix', '0'))
        except ValueError:
            flash('La durée et le prix doivent être des nombres valides.', 'danger')
            return redirect(url_for('formateur'))
        if not all([formateur_nom, formateur_email, titre, categorie, description, live_date, live_time, live_url]):
            flash('Tous les champs obligatoires doivent être remplis.', 'danger')
            return redirect(url_for('formateur'))
        parsed_url = urlparse(live_url)
        if (
            niveau not in {'Débutant', 'Intermédiaire', 'Professionnel'}
            or not 1 <= duree_jours <= 365
            or not 15000 <= prix <= 90000
            or parsed_url.scheme not in {'http', 'https'}
            or not parsed_url.netloc
        ):
            flash('Vérifiez le niveau, la durée, le prix et le lien du direct.', 'danger')
            return redirect(url_for('formateur'))
        course = Course(
            titre=titre, categorie=categorie, niveau=niveau, duree_jours=duree_jours,
            public_cible='À définir', modalite='En ligne', description=description,
            prix=prix, statut='En attente', validation_status='En attente',
            formateur_nom=formateur_nom, formateur_email=formateur_email,
            live_date=live_date, live_time=live_time, live_url=live_url,
        )
        db.session.add(course)
        db.session.commit()
        flash('Formation envoyée. Elle sera visible après validation par ACADD.', 'success')
        return redirect(url_for('formateur'))
    content = render_template_string(HTML_FORMATEUR)
    return render_template_string(HTML_BASE, body_content=content)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('code') != os.environ.get('ADMIN_CODE', 'ACADD2026'):
            flash('Code administrateur incorrect.', 'danger')
            return redirect(url_for('admin'))
        session['is_admin'] = True
        return redirect(url_for('admin'))
    if not session.get('is_admin'):
        content = """
        <div class="row justify-content-center"><div class="col-md-5"><div class="card border-0 shadow-sm rounded-4 p-4">
        <h2 class="fw-bold">Accès administrateur ACADD</h2><p class="text-muted">Entrez le code de validation.</p>
        <form method="POST"><input type="password" name="code" class="form-control mb-3" placeholder="Code administrateur" required><button class="btn btn-acadd w-100">Se connecter</button></form>
        </div></div></div>
        """
        return render_template_string(HTML_BASE, body_content=content)
    pending = Course.query.filter_by(validation_status='En attente').order_by(Course.id.desc()).all()
    payments = PaymentRequest.query.filter_by(statut='À vérifier').order_by(PaymentRequest.date_demande.desc()).all()
    content = render_template_string(HTML_ADMIN, pending=pending, payments=payments)
    return render_template_string(HTML_BASE, body_content=content)


@app.route('/admin/formation/<int:course_id>/<action>', methods=['POST'])
def moderate_course(course_id, action):
    if not session.get('is_admin'):
        flash('Accès administrateur requis.', 'danger')
        return redirect(url_for('admin'))
    course = Course.query.get_or_404(course_id)
    if course.validation_status != 'En attente' or action not in {'valider', 'refuser'}:
        flash('Action de validation invalide.', 'danger')
        return redirect(url_for('admin'))
    course.validation_status = 'Approuvée' if action == 'valider' else 'Refusée'
    course.statut = 'Ouvert' if action == 'valider' else 'Refusée'
    db.session.commit()
    flash('Formation publiée.' if action == 'valider' else 'Formation refusée.', 'success' if action == 'valider' else 'warning')
    return redirect(url_for('admin'))


@app.route('/admin/paiement/<int:payment_id>/<action>', methods=['POST'])
def moderate_payment(payment_id, action):
    if not session.get('is_admin'):
        flash('Accès administrateur requis.', 'danger')
        return redirect(url_for('admin'))
    payment = PaymentRequest.query.get_or_404(payment_id)
    if payment.statut != 'À vérifier' or action not in {'autoriser', 'refuser'}:
        flash('Action de paiement invalide.', 'danger')
        return redirect(url_for('admin'))
    if action == 'autoriser':
        existing = Enrollment.query.filter_by(user_id=payment.user_id, course_id=payment.course_id).first()
        if not existing:
            db.session.add(Enrollment(
                user_id=payment.user_id,
                course_id=payment.course_id,
                progress=0,
                statut='Accès autorisé',
            ))
        payment.statut = 'Accès autorisé'
        flash('Paiement confirmé : accès au cours autorisé.', 'success')
    else:
        payment.statut = 'Refusé'
        flash('Paiement refusé : accès non accordé.', 'warning')
    db.session.commit()
    return redirect(url_for('admin'))


def init_db():
    with app.app_context():
        db.create_all()

        user_columns = {column['name'] for column in inspect(db.engine).get_columns('user')}
        if 'niveau' not in user_columns:
            db.session.execute(text(
                "ALTER TABLE user ADD COLUMN niveau VARCHAR(50) NOT NULL DEFAULT 'Débutant'"
            ))
            db.session.commit()

        course_columns = {column['name'] for column in inspect(db.engine).get_columns('course')}
        migrations = {
            'formateur_nom': "ALTER TABLE course ADD COLUMN formateur_nom VARCHAR(120)",
            'formateur_email': "ALTER TABLE course ADD COLUMN formateur_email VARCHAR(120)",
            'validation_status': "ALTER TABLE course ADD COLUMN validation_status VARCHAR(50) NOT NULL DEFAULT 'Approuvée'",
            'live_date': "ALTER TABLE course ADD COLUMN live_date VARCHAR(20)",
            'live_time': "ALTER TABLE course ADD COLUMN live_time VARCHAR(10)",
            'live_url': "ALTER TABLE course ADD COLUMN live_url VARCHAR(500)",
        }
        for column, statement in migrations.items():
            if column not in course_columns:
                db.session.execute(text(statement))
        db.session.commit()

        if not Course.query.first():
            courses = [
                Course(
                    titre='Culture numérique & citoyenneté digitale',
                    categorie='Numérique',
                    niveau='Débutant',
                    duree_jours=2,
                    public_cible='Grand public',
                    modalite='En ligne + mentorat',
                    description='Découvrez les usages du numérique, la sécurité en ligne, la citoyenneté numérique et les outils indispensables au quotidien.',
                    prix=15000,
                    statut='Ouvert'
                ),
                Course(
                    titre='Initiation à l’IA générative',
                    categorie='IA',
                    niveau='Débutant',
                    duree_jours=3,
                    public_cible='Tous',
                    modalite='En ligne asynchrone',
                    description='Apprenez à utiliser les outils d’IA pour la recherche, la création de contenu, l’analyse rapide et l’automatisation de tâches.',
                    prix=25000,
                    statut='Populaire'
                ),
                Course(
                    titre='Créer un site web avec WordPress',
                    categorie='Web',
                    niveau='Intermédiaire',
                    duree_jours=4,
                    public_cible='Tous',
                    modalite='En ligne',
                    description='Créez un site web professionnel, personnalisez le design et publiez votre présence en ligne sans savoir coder.',
                    prix=45000,
                    statut='À venir'
                ),
                Course(
                    titre='Marketing digital & réseaux sociaux',
                    categorie='Marketing',
                    niveau='Intermédiaire',
                    duree_jours=3,
                    public_cible='Entrepreneurs',
                    modalite='En ligne',
                    description='Développez une stratégie marketing sur les réseaux sociaux, pilotez des campagnes et mesurez les résultats.',
                    prix=60000,
                    statut='À venir'
                ),
                Course(
                    titre='Sécurité informatique pour tous',
                    categorie='Cybersécurité',
                    niveau='Débutant',
                    duree_jours=2,
                    public_cible='Tout public',
                    modalite='En ligne',
                    description='Comprenez les bons réflexes pour sécuriser ses comptes, ses données et ses appareils personnels.',
                    prix=30000,
                    statut='Ouvert'
                ),
                Course(
                    titre='Automation des tâches avec AI & outils no-code',
                    categorie='Productivité',
                    niveau='Professionnel',
                    duree_jours=5,
                    public_cible='Professionnels',
                    modalite='En ligne live',
                    description='Automatisez les tâches répétitives en utilisant l’IA et des outils no-code pour gagner du temps et améliorer la productivité.',
                    prix=90000,
                    statut='Nouveau'
                ),
            ]

            db.session.add_all(courses)
            db.session.commit()

            step_templates = [
                ('Culture numérique & citoyenneté digitale', [
                    ('Découvrir le numérique', 25, 'Comprendre les bases', 'Introduction au numérique et à son impact dans la vie quotidienne.'),
                    ('Sécurité en ligne', 35, 'Pratique', 'Créer des mots de passe sûrs et protéger ses informations personnelles.'),
                    ('Citoyenneté digitale', 30, 'Atelier', 'Comprendre les droits, les devoirs et les usages responsables du numérique.')
                ]),
                ('Initiation à l’IA générative', [
                    ('Les bases de l’IA', 30, 'Cours', 'Comprendre le fonctionnement simple et utile des systèmes d’intelligence artificielle.'),
                    ('Utiliser ChatGPT et outils IA', 45, 'Pratique', 'Rédiger, résumer, rechercher et générer des idées avec efficacité.'),
                    ('Cas d’usage professionnels', 35, 'Projet', 'Identifier les usages utiles de l’IA au travail et dans l’éducation.')
                ]),
                ('Créer un site web avec WordPress', [
                    ('Installer WordPress', 30, 'Guide', 'Déployer un site localement et configurer les premiers paramètres.'),
                    ('Créer des pages & contenus', 45, 'Pratique', 'Structurer un site, écrire des contenus et organiser une navigation claire.'),
                    ('Personnaliser et publier', 40, 'Projet', 'Choisir un thème, optimiser le site et le mettre en ligne.')
                ]),
                ('Marketing digital & réseaux sociaux', [
                    ('Stratégie marketing', 30, 'Cours', 'Définir un plan d’action autour de vos objectifs clients.'),
                    ('Réseaux sociaux', 40, 'Atelier', 'Produire un contenu engageant et cohérent par canal.'),
                    ('Mesure de performance', 20, 'Analyse', 'Suivre les indicateurs clés et ajuster la stratégie.')
                ]),
                ('Sécurité informatique pour tous', [
                    ('Risques et menaces', 25, 'Cours', 'Identifier les cybermenaces classiques et les signes d’alerte.'),
                    ('Protection des comptes', 30, 'Pratique', 'Mettre en place une meilleure sécurité sur les identités numériques.'),
                    ('Bonnes pratiques', 25, 'Atelier', 'Adopter des habitudes sûres pour protéger ses appareils et ses données.')
                ]),
                ('Automation des tâches avec AI & outils no-code', [
                    ('Identifier les tâches répétitives', 30, 'Diagnostic', 'Repérer les tâches qui peuvent être automatisées.'),
                    ('Construire des workflows', 45, 'Pratique', 'Créer des flux de travail simples à l’aide d’outils no-code.'),
                    ('Pilotage et optimisation', 35, 'Projet', 'Mettre en place des indicateurs et améliorer progressivement les processus.')
                ]),
            ]

            for course in courses:
                entry = step_templates.pop(0) if step_templates else None
                if entry and entry[0] == course.titre:
                    for idx, (title, duration, kind, desc) in enumerate(entry[1], start=1):
                        step = CourseStep(
                            course_id=course.id,
                            ordre=idx,
                            titre=title,
                            duree_min=duration,
                            type_module=kind,
                            description=desc,
                        )
                        db.session.add(step)
            db.session.commit()

        prices_and_levels = {
            'Culture numérique & citoyenneté digitale': (15000, 'Débutant'),
            'Initiation à l’IA générative': (25000, 'Débutant'),
            'Créer un site web avec WordPress': (45000, 'Intermédiaire'),
            'Marketing digital & réseaux sociaux': (60000, 'Intermédiaire'),
            'Sécurité informatique pour tous': (30000, 'Débutant'),
            'Automation des tâches avec AI & outils no-code': (90000, 'Professionnel'),
        }
        for title, (price, level) in prices_and_levels.items():
            course = Course.query.filter_by(titre=title).first()
            if course:
                course.prix = price
                course.niveau = level
        db.session.commit()


if __name__ == '__main__':
    init_db()
    print('Application ACADD Learning démarrée sur http://127.0.0.1:5000')
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', '5000')),
        debug=os.environ.get('FLASK_DEBUG', '').lower() == 'true',
    )
