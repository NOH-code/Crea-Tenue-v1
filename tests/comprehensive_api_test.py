import os
import io
import google.generativeai as genai
from PIL import Image
import traceback

# --- Configuration ---
API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyARZh0xpf9z856HnMQUSjU0JMK_4i3qamg')
TEXT_MODEL = 'gemini-2.5-flash'
IMAGE_MODEL = 'gemini-2.5-flash-image'
OUTPUT_IMAGE_FILENAME = "generated_test_image.png"

def setup_api():
    """Configures the Gemini API."""
    if not API_KEY:
        print("[ERROR] GOOGLE_API_KEY not found. Please set it as an environment variable.")
        return False
    try:
        genai.configure(api_key=API_KEY)
        print("[OK] Google Gemini API configured successfully.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to configure API: {e}")
        return False

def test_text_generation():
    """Tests the text generation capability of a standard Gemini model."""
    print("\n--- Testing Text Generation ---")
    try:
        model = genai.GenerativeModel(TEXT_MODEL)
        prompt = "Hello, Gemini! In one sentence, confirm that you are operational."
        response = model.generate_content(prompt)
        
        if response.text:
            print(f"[SUCCESS] Text model '{TEXT_MODEL}' responded:")
            print(f"  -> \"{response.text.strip()}\"")
            return True
        else:
            print("[FAILED] Text model did not return any text.")
            return False
    except Exception as e:
        print(f"[FAILED] An error occurred during text generation: {e}")
        traceback.print_exc()
        return False

def test_image_generation():
    """Tests the image generation capability and saves the output."""
    print("\n--- Testing Image Generation ---")
    try:
        model = genai.GenerativeModel(IMAGE_MODEL)
        prompt = "A photorealistic image of an astronaut riding a horse on Mars, digital art."
        
        # Create a dummy image to send with the prompt, as the API expects multimodal input
        dummy_image = Image.new('RGB', (100, 100), (255, 255, 255))
        
        print(f"[INFO] Sending prompt to '{IMAGE_MODEL}' model...")
        response = model.generate_content([prompt, dummy_image])
        
        if response.candidates and response.candidates[0].content.parts:
            image_part = response.candidates[0].content.parts[0]
            if hasattr(image_part, 'inline_data'):
                # Save the raw response for debugging
                with open("api_response.txt", "w") as f:
                    f.write(str(image_part.inline_data))
                print("[INFO] Raw API response saved to 'api_response.txt'")

                image_data = image_part.inline_data.data
                
                # Create an image object from the data
                image = Image.open(io.BytesIO(image_data))
                
                # Save the image
                image.save(OUTPUT_IMAGE_FILENAME, "PNG")
                
                print(f"[SUCCESS] Image generated and saved as '{OUTPUT_IMAGE_FILENAME}'")
                
                # Verify file
                if os.path.exists(OUTPUT_IMAGE_FILENAME) and os.path.getsize(OUTPUT_IMAGE_FILENAME) > 1000:
                    print(f"[OK] File '{OUTPUT_IMAGE_FILENAME}' verified successfully.")
                    return True
                else:
                    print("[FAILED] Image file is missing or empty after generation.")
                    return False
        
        print("[FAILED] No image data found in the API response.")
        return False
    except Exception as e:
        print(f"[FAILED] An error occurred during image generation: {e}")
        traceback.print_exc()
        return False

def main():
    """Main function to run all tests."""
    print("=====================================")
    print("  Running Gemini API Test Suite")
    print("=====================================")
    
    if not setup_api():
        return
        
    text_ok = test_text_generation()
    image_ok = test_image_generation()
    
    print("\n--- Test Summary ---")
    print(f"Text Generation: {'PASSED' if text_ok else 'FAILED'}")
    print(f"Image Generation: {'PASSED' if image_ok else 'FAILED'}")
    print("=====================================")
    
    if not (text_ok and image_ok):
        exit(1)

if __name__ == "__main__":
    main()
