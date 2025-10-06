import os
import base64
from google.cloud import aiplatform
import traceback

# --- Configuration ---
PROJECT_ID = "test-nanobanana-474308"
LOCATION = "europe-west1"
os.environ.setdefault('GOOGLE_APPLICATION_CREDENTIALS', 'backend/gcp-key.json')

MODEL_NAME = "imagegeneration@006"
OUTPUT_FILENAME = "vertex_ai_test_image.png"

def test_vertex_ai_image_generation():
    """
    Tests image generation using the Google Cloud Vertex AI API.
    """
    print("=============================================")
    print("  Testing Vertex AI Image Generation (Imagen)")
    print("=============================================")

    if not os.path.exists(os.environ['GOOGLE_APPLICATION_CREDENTIALS']):
        print(f"[ERROR] GCP key file not found at '{os.environ['GOOGLE_APPLICATION_CREDENTIALS']}'.")
        return False
    
    print(f"[OK] Project ID: {PROJECT_ID}")
    print(f"[OK] Location: {LOCATION}")
    print(f"[OK] Credentials file found.")

    try:
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        client_options = {"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
        prediction_client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
        print("[OK] Vertex AI client initialized.")

        endpoint = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_NAME}"
        
        prompt = "A majestic lion wearing a crown, sitting on a throne, fantasy digital art, high detail."
        print(f"\n[INFO] Prompt: \"{prompt}\"")

        # The structure for the request payload in Python is slightly different from Node.js
        # We need to create a dict that can be serialized.
        instance = {"prompt": prompt}
        instances = [instance]
        
        parameters = {
            "sampleCount": 1,
            "aspectRatio": "1:1",
            "negativePrompt": "blurry, low quality",
        }
        
        print("[OK] API request payload created.")
        print("[INFO] Sending request to Vertex AI API... (This may take a moment)")
        
        response = prediction_client.predict(
            endpoint=endpoint, instances=instances, parameters=parameters
        )
        
        print("[OK] API response received.")

        if not response.predictions:
            print("[FAILED] The API returned no predictions.")
            return False

        prediction = response.predictions[0]
        base64_image = prediction.get("bytesBase64Encoded")

        if not base64_image:
            print("[FAILED] No image data found in the API response.")
            return False

        image_bytes = base64.b64decode(base64_image)
        
        with open(OUTPUT_FILENAME, "wb") as f:
            f.write(image_bytes)
        
        if os.path.exists(OUTPUT_FILENAME) and os.path.getsize(OUTPUT_FILENAME) > 1000:
            print(f"\n[SUCCESS] Image successfully generated and saved as '{OUTPUT_FILENAME}'")
            return True
        else:
            print("[FAILED] File was not saved correctly or is empty.")
            return False

    except Exception as e:
        print(f"\n[FAILED] An error occurred during the test: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vertex_ai_image_generation()
    print("=============================================")
    if not success:
        exit(1)
