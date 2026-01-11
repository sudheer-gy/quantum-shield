#include <openssl/rsa.h>

void generate_legacy_keys() {
    // BAD: Old C++ Banking code often looks like this
    RSA *rsa = RSA_generate_key(2048, RSA_F4, NULL, NULL);
}