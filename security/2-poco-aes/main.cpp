#include <string>
#include <memory>
#include <stdexcept>
#include <Poco/Crypto/Cipher.h>
#include <Poco/Crypto/CipherKey.h>
#include <Poco/Crypto/CipherFactory.h>
#include <Poco/RandomStream.h>
#include <Poco/Random.h>
#include <iostream>

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
        throw std::runtime_error("The message is too short");
    }
    const auto begin = reinterpret_cast<const unsigned char *>(&message[0]);
    key.setIV({begin, begin + ivSize});
    Poco::Crypto::Cipher::Ptr cipher(Poco::Crypto::CipherFactory::defaultFactory().createCipher(key));

    return cipher->decryptString(message.substr(ivSize));
}

int main()
{
    Poco::Crypto::CipherKey::ByteVec keyBytes(16);
    Poco::RandomInputStream ris;
    ris.read(reinterpret_cast<char *>(&keyBytes[0]), keyBytes.size());

    std::string result = encodeAES(keyBytes, "123");

    // result[0] = '0';

    std::cout << result.size() << std::endl;

    try
    {
        std::cout << decodeAES(keyBytes, result) << std::endl;
    }
    catch (const std::exception &e)
    {
        std::cerr << "Caught an exception: " << e.what() << std::endl;
    }

    return 0;
}
