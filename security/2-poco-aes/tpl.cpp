std::string encodeAES(const Poco::Crypto::CipherKey::ByteVec &aesKey, const std::string &message)
{
    Poco::Crypto::CipherKey key("aes-128-cbc");
    key.setKey({aesKey.begin(), aesKey.end()});

    const std::string initializationVector{key.getIV().begin(), key.getIV().end()};
    const std::unique_ptr<Poco::Crypto::Cipher> cipher(
        Poco::Crypto::CipherFactory::defaultFactory().createCipher(key));
    return initializationVector + cipher->encryptString(message);
}

std::string decodeAES(const Poco::Crypto::CipherKey::ByteVec &aesKey, const std::string &message)
{
    Poco::Crypto::CipherKey key("aes-128-cbc");
    key.setKey({aesKey.begin(), aesKey.end()});

    auto ivSize = static_cast<std::size_t>(key.ivSize());
    if (message.size() <= ivSize)
    {
        throw yexception() << "The message is too short";
    }
    const auto begin = reinterpret_cast<const unsigned char *>(&message[0]);
    key.setIV({begin, begin + ivSize});
    Poco::Crypto::Cipher::Ptr cipher(Poco::Crypto::CipherFactory::defaultFactory().createCipher(key));

    return cipher->decryptString(message.substr(ivSize));
}