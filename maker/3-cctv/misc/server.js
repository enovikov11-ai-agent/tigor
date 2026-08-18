const key = await crypto.subtle.generateKey(
    { name: "AES-CTR", length: 256 },
    true,
    ["encrypt", "decrypt"]
);

const iv = crypto.getRandomValues(new Uint8Array(16));  // 128-bit nonce
const ciphertext = await crypto.subtle.encrypt(
    {
        name: "AES-CTR",
        counter: iv,         // acts like IV
        length: 64           // bits of counter (recommend 64–128)
    },
    key,
    chunkBuffer
);

// Import RSA public key (SPKI format)
const publicKey = await crypto.subtle.importKey(
    "spki",
    publicKeyBuffer,
    {
        name: "RSA-OAEP",
        hash: "SHA-256"
    },
    false,
    ["encrypt"]
);

// Encrypt AES-GCM key
const encryptedKey = await crypto.subtle.encrypt(
    {
        name: "RSA-OAEP"
    },
    publicKey,
    aesKeyBuffer  // Uint8Array of exported raw AES key
);

