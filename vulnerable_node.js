const crypto = require('crypto');

// BAD: Modern Node.js app using weak crypto
crypto.generateKeyPair('rsa', {
  modulusLength: 2048,
}, (err, publicKey, privateKey) => {
  console.log('Keys generated');
});