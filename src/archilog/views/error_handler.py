import logging
from flask import render_template, flash, redirect, url_for

def register_error_handlers(app):
    """Enregistre les gestionnaires d'erreurs pour l'application Flask."""

    # 🔹 Gestion des erreurs 404 (Page non trouvée)
    @app.errorhandler(404)
    def page_not_found(error):
        """Gérer les erreurs 404 et logguer l'événement"""
        logging.warning(f"⚠️ 404 - Page non trouvée : {error}")
        flash("La page demandée est introuvable.", "warning")  # Message utilisateur
        return render_template("404.html"), 404  # Retourne une page personnalisée

    # 🔹 Gestion des erreurs 500 (Erreur interne du serveur)
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Gérer les erreurs 500 et logguer l'événement"""
        logging.critical(f"🔥 Erreur interne du serveur : {error}", exc_info=True)
        flash("Erreur interne du serveur", "error")  # Message utilisateur
        return redirect(url_for("index.html"))  # Redirection vers la page d'accueil
