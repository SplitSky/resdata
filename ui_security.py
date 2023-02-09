# cryptography module
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding, rsa

class ui_security(object):
    def __init__(self, username_in : str, password_in : str):
        self.username = username_in
        self.password = password_in
        self.public_file_name = 'publicKeyFile.pem'
        self.private_file_name = 'privateKeyFile.pem'

    def generate_keys(self):
        private_key = rsa.generate_private_key(public_exponent=65337, key_size=2048, backend=default_backend())
        public_key = private_key.public_key()
        self.save_keys(private_key,public_key)
        return private_key, public_key

    def convert_keys_for_storage(self, private_key, public_key):
        pem = private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
        pem2 = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
        return pem,pem2

    def save_keys(self, private_key, public_key):
        pem, pem2 = self.convert_keys_for_storage(private_key, public_key)
        
        with open(self.private_file_name, 'wb') as f:
            f.write(pem)
            f.close()

        with open(self.public_file_name, 'wb') as f:
            f.write(pem2)
            f.close()
        
    def read_keys(self):
        with open(self.private_file_name, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),password=None, backend=default_backend()
            )
            f.close()
        with open(self.public_file_name, "rb") as f:
            public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )
        return private_key, public_key

    def encrypt_message(self,message, public_key):
        return public_key.encrypt(message,
                                       padding.OAEP(
                                                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                algorithm=hashes.SHA256(),label=None
                                            )
                                        )
    def decrypt_message(self, message, private_key):
        return private_key.decrypt(message, 
                                   padding.OAEP(mgf=padding.MGF1(
                                                    algorithm=hashes.SHA256()),
                                                algorithm=hashes.SHA256(),
                                                label=None)
                                   )

    def get_signed_message(self, private_key, ui_public_key, message):
        final_message = self.decrypt_message(message, private_key)
        return self.decrypt_message(final_message, ui_public_key)

    def encrypt_and_sign_message(self, public_key, ui_private_key, message):
        # sign
        message_final = self.encrypt_message(message, ui_private_key) 
        # encrypt
        return self.encrypt_message(message_final, public_key)
