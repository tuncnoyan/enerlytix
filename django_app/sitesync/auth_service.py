"""Authentication-related helper services for invitations and password reset flows."""

from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string


def _brand_context():
    """Return common branding fields used by auth templates."""

    return {
        "brand_name": "Enerlytix",
        "support_reply_to": (getattr(settings, "MAIL_REPLY_TO", "") or "").strip(),
    }


def build_invitation_email(request, invitation):
    """Build a branded invitation email with text + HTML alternatives."""

    accept_url = request.build_absolute_uri(
        f"/invitations/{invitation.id}/accept/"
    )
    context = {
        **_brand_context(),
        "recipient_email": invitation.email,
        "action_url": accept_url,
        "invitation": invitation,
        "invited_by": request.user,
    }

    subject = render_to_string(
        "emails/sitesync/invitation_email_subject.txt", context
    ).strip()
    text_body = render_to_string("emails/sitesync/invitation_email.txt", context)
    html_body = render_to_string("emails/sitesync/invitation_email.html", context)

    message = EmailMessage(
        subject=subject,
        body=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "hello@demomailtrap.co"),
        to=[invitation.email],
        reply_to=[context["support_reply_to"]] if context["support_reply_to"] else None,
    )
    message.content_subtype = "plain"
    message.esp_extra = {
        "category": "User Invitation",
        "custom_variables": {
            "invitation_id": str(invitation.id),
            "invited_by": request.user.get_username(),
            "html_preview": html_body,
        },
    }
    return message, accept_url


def send_admin_password_recovery_email(request, user) -> bool:
    """Send a one-time password recovery link (single-use token) for an existing user."""

    email = (getattr(user, "email", "") or "").strip()
    if not email:
        return False

    form = PasswordResetForm(data={"email": email})
    if not form.is_valid():
        return False

    form.save(
        request=request,
        use_https=request.is_secure(),
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "hello@demomailtrap.co"),
        email_template_name="registration/password_reset_email.txt",
        html_email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
        extra_email_context={"brand_name": "Enerlytix"},
    )
    return True
