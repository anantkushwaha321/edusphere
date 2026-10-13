from django.urls import path
from . import views

app_name = 'compliance'

urlpatterns = [
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
    path('cookie-policy/', views.cookie_policy_view, name='cookie_policy'),
    path('refund-policy/', views.refund_policy_view, name='refund_policy'),
    path('accessibility-statement/', views.accessibility_statement_view, name='accessibility_statement'),

    # Interactive Cookie Consent API
    path('api/cookie-consent/', views.cookie_consent_api, name='cookie_consent_api'),

    # GDPR / CCPA Data Subject Requests (DSAR)
    path('privacy/data-portal/', views.data_subject_portal_view, name='data_portal'),
    path('privacy/export-data/', views.export_my_data_instant, name='export_data'),

    # Email Preferences & 1-Click Unsubscribe
    path('settings/email-preferences/', views.email_preferences_view, name='email_preferences'),
    path('unsubscribe/<uuid:token>/', views.unsubscribe_token_view, name='unsubscribe_token'),

    # COPPA & Parental Consent
    path('parental-consent/', views.parental_consent_view, name='parental_consent'),
]
