# config/nats.py

import ssl


def create_tls_config():
    context = ssl.create_default_context()
    context.load_cert_chain(
        certfile="mtls/client.crt",
        keyfile="mtls/client.key",
    )
    context.load_verify_locations("mtls/ca.crt")
    return context