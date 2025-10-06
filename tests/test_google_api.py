import google.generativeai as genai
import os

# Remplacez par votre clé API
GOOGLE_API_KEY = "AIzaSyARZh0xpf9z856HnMQUSjU0JMK_4i3qamg"

def test_google_api():
    try:
        # Configuration de l'API    
        genai.configure(api_key=GOOGLE_API_KEY)

        # Test avec un modèle de texte simple
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Prompt de test simple
        response = model.generate_content("Bonjour, pouvez-vous me dire si cette API fonctionne ? Répondez en une phrase.")

        print("Test reussi !")
        print("Reponse de l'API :", response.text)
        return True

    except Exception as e:
        print("Erreur lors du test :", str(e))
        return False

if __name__ == "__main__":
    test_google_api()