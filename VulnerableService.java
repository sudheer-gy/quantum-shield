import java.security.KeyPairGenerator;
import java.security.NoSuchAlgorithmException;

public class VulnerableService {
    public void createKey() throws NoSuchAlgorithmException {
        // BAD: This is vulnerable to Quantum attacks
        KeyPairGenerator keyGen = KeyPairGenerator.getInstance("RSA");
        keyGen.initialize(2048);
    }
}