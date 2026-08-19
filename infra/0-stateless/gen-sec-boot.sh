# 123123

set -euo pipefail

KEYDIR="$HOME/.ssh/secureboot"

mkdir -p "$KEYDIR"
chmod 700 "$KEYDIR"
cd "$KEYDIR"
umask 077

openssl genpkey \
  -algorithm RSA \
  -pkeyopt rsa_keygen_bits:3072 \
  -aes-256-cbc \
  -out PK.key

openssl req \
  -new \
  -x509 \
  -key PK.key \
  -sha256 \
  -days 3650 \
  -subj "/CN=Tigor Secure Boot Platform Key/" \
  -out PK.crt

openssl genpkey \
  -algorithm RSA \
  -pkeyopt rsa_keygen_bits:3072 \
  -aes-256-cbc \
  -out KEK.key

openssl req \
  -new \
  -x509 \
  -key KEK.key \
  -sha256 \
  -days 3650 \
  -subj "/CN=Tigor Secure Boot KEK/" \
  -out KEK.crt

openssl genpkey \
  -algorithm RSA \
  -pkeyopt rsa_keygen_bits:3072 \
  -aes-256-cbc \
  -out db.key

openssl req \
  -new \
  -x509 \
  -key db.key \
  -sha256 \
  -days 3650 \
  -subj "/CN=Tigor Secure Boot db Image Signing/" \
  -out db.crt

for name in PK KEK db; do
  openssl x509 \
    -in "$name.crt" \
    -outform DER \
    -out "$name.cer"
done

chmod 600 ./*.key ./*.crt ./*.cer

echo
echo "Generated:"
ls -l "$KEYDIR"
