
# worked, from https://www.youtube.com/watch?v=ZbrJjkOX8Ro
# Skips hostname verification, Ignores all certificate validation errors 
# Vulnerable to man-in-the-middle (MITM) attacks since no certificate checks are performed 
# use for development only when DEBUG = True, Security Risk, Not Production-Safe

import ssl

from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.utils.functional import cached_property

class CustomBackend(SMTPBackend):
	@cached_property
	def ssl_context(self):
		if self.ssl_certfile or self.ssl_keyfile:
			ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
			ssl_context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)
			return ssl_context
		else:
			ssl_context = ssl.create_default_context()
			ssl_context.check_hostname = False # Skips verifying if the server’s certificate matches the hostname (e.g., smtp.gmail.com).
			ssl_context.verify_mode = ssl.CERT_NONE # Ignores certificate validation errors, including mismatched certificates or untrusted Certificate Authorities (CAs).
			return ssl_context





"""
# by gemini, worked
# Disables strict X.509 certificate validation (e.g., warnings about non-critical basicConstraints in CA certificates).
# Still performs minimal checks (e.g., hostname verification and chain trust).
import ssl
from django.core.mail.backends.smtp import EmailBackend

class LenientSMTPBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False
        try:
            # Get the default SSL context
            context = ssl.create_default_context()

            # *** Modify the context to remove the strict verification flag ***
            # This is the key change to address the Python 3.13 strictness
            context.verify_flags &= ~ssl.VERIFY_X509_STRICT
            
            connection = super(EmailBackend, self).open() # Call the parent's open without args initially

            if connection:
                if self.use_tls:
                    self.connection.starttls(context=context) # Use the modified context here
                elif self.use_ssl:
                     # Use the modified context here for SSL as well
                    self.connection = ssl.wrap_socket(self.connection, ssl_version=ssl.PROTOCOL_SSLv23, context=context)

                if self.username and self.password:
                    self.connection.login(self.username, self.password)
                return True
            return False
        except Exception:
            if not self.fail_silently:
                raise
"""




"""
# ignore:
# settings.py

# ... other settings ...

##############################################################################################
import os
#the email settings

# Use the lenient backend only in debug mode
if DEBUG:
    EMAIL_BACKEND = 'app1.backends.email_backend.LenientSMTPBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "MY APP"
EMAIL_HOST_USER =  "anup30coc@gmail.com" # os.environ.get("AA_EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = "wapr ajyp hudc bqoj" # os.environ.get("AA_EMAIL_HOST_PASSWORD")

# ... other settings ...

"""