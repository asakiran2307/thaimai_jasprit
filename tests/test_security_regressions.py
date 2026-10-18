"""Regression checks for security-sensitive application configuration.

These tests intentionally avoid importing the Flask app, which would require live
database configuration and installed application dependencies.
"""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "index.py").read_text(encoding="utf-8")


class SecurityRegressionTests(unittest.TestCase):
    def test_dict_loader_is_imported_before_template_loader_setup(self):
        self.assertIn("from jinja2 import BaseLoader, DictLoader, TemplateNotFound", SOURCE)
        self.assertIn("app.jinja_loader = DictLoader(TEMPLATES)", SOURCE)

    def test_database_credentials_are_loaded_from_environment(self):
        self.assertIn('os.environ.get("DATABASE_URL"', SOURCE)
        self.assertNotIn("postgresql://neondb_owner:", SOURCE)

    def test_production_secret_key_must_be_configured(self):
        self.assertIn('os.environ.get("SECRET_KEY")', SOURCE)
        self.assertIn('SECRET_KEY must be configured in production.', SOURCE)
        self.assertNotIn("a_very_secret_key_for_maternal_health_app", SOURCE)

    def test_session_cookie_protections_are_enabled(self):
        self.assertIn('app.config["SESSION_COOKIE_HTTPONLY"] = True', SOURCE)
        self.assertIn('app.config["SESSION_COOKIE_SAMESITE"] = "Lax"', SOURCE)
        self.assertIn('app.config["SESSION_COOKIE_SECURE"] = APP_ENV == "production"', SOURCE)

    def test_doctor_login_checks_password_hash(self):
        self.assertIn("if doctor and check_password_hash(doctor.password_hash, password):", SOURCE)
        self.assertNotIn("if doctor and doctor.mobile == password:", SOURCE)

    def test_ai_endpoint_validates_and_bounds_history(self):
        self.assertIn("data = request.get_json(silent=True)", SOURCE)
        self.assertIn("if not isinstance(data, dict):", SOURCE)
        self.assertIn("if len(user_input) > 4000:", SOURCE)
        self.assertIn("for item in raw_history[-20:]:", SOURCE)
        self.assertIn("Chat history contains an invalid message.", SOURCE)

    def test_stored_doula_chat_is_html_escaped(self):
        self.assertIn("{{ log.content }}", SOURCE)
        self.assertNotIn("{{ log.content|safe }}", SOURCE)

    def test_demo_accounts_are_not_seeded_in_production_by_default(self):
        self.assertIn('"true" if APP_ENV != "production" else "false"', SOURCE)
        self.assertIn('if not Doctor.query.first() and SEED_DEMO_DATA:', SOURCE)
        self.assertIn('os.environ.get("INITIAL_DOCTOR_PASSWORD"', SOURCE)
        self.assertIn('os.environ.get("INITIAL_PATIENT_PASSWORD"', SOURCE)

    def test_development_server_debug_is_disabled_in_production(self):
        self.assertIn('app.run(debug=APP_ENV != "production")', SOURCE)

    def test_upload_size_is_bounded(self):
        self.assertIn('app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))', SOURCE)
        self.assertIn('file.read(app.config["MAX_CONTENT_LENGTH"] + 1)', SOURCE)


if __name__ == "__main__":
    unittest.main()
