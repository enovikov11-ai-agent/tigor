#!/bin/bash
# Generate client certificate for tgr.rs access control
# This creates a self-signed client certificate that Caddy will trust

set -e

CERT_NAME="tgr-mtls"

echo "Generating client certificate: $CERT_NAME"

# Generate private key and self-signed certificate with client auth extension
# Using RSA 4096 for universal compatibility (macOS, iOS, all browsers)
openssl req -x509 -newkey rsa:4096 \
  -keyout "${CERT_NAME}.key" \
  -out "${CERT_NAME}.crt" \
  -days 365 -nodes \
  -subj "/CN=${CERT_NAME}.tgr.rs" \
  -addext "keyUsage=digitalSignature,keyEncipherment" \
  -addext "extendedKeyUsage=clientAuth"

# Create PKCS12 bundle for browser/device import
echo "Creating PKCS12 bundle..."
openssl pkcs12 -export \
  -inkey "${CERT_NAME}.key" \
  -in "${CERT_NAME}.crt" \
  -out "${CERT_NAME}.p12" \
  -name "tgr.rs ${CERT_NAME}"

# Display certificate info
echo ""
echo "Certificate details:"
openssl x509 -in "${CERT_NAME}.crt" -noout -subject -dates -ext extendedKeyUsage

# Organize files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CADDY_DIR="${SCRIPT_DIR}/../../prod/caddy"
DOCS_DIR="${HOME}/Documents"

echo ""
echo "Installing files..."

# Remove old .p12 if exists, then move new one
rm -f "${DOCS_DIR}/${CERT_NAME}.p12"
mv "${CERT_NAME}.p12" "${DOCS_DIR}/${CERT_NAME}.p12"
echo "✓ ${DOCS_DIR}/${CERT_NAME}.p12"

# Remove old .crt if exists, then move new one
rm -f "${CADDY_DIR}/${CERT_NAME}.crt"
mv "${CERT_NAME}.crt" "${CADDY_DIR}/${CERT_NAME}.crt"
echo "✓ ${CADDY_DIR}/${CERT_NAME}.crt"

# Remove .key (it's included in .p12)
rm "${CERT_NAME}.key"

echo ""
echo "✅ Done! Files installed."
echo ""
echo "Next steps:"
echo "  1. Deploy monorepo to update Caddy configuration"
echo "  2. Import ${DOCS_DIR}/${CERT_NAME}.p12 into your browser/device"
echo "  3. Visit https://p-files.tgr.rs to test"
echo ""
echo "⚠️  Backup ${DOCS_DIR}/${CERT_NAME}.p12 securely!"
