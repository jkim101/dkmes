from google.cloud import aiplatform
import os
from dotenv import load_dotenv

load_dotenv(".env.local")

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = "us-central1"

aiplatform.init(project=project_id, location=location)

print(f"Listing models for project {project_id} in {location}...")

from vertexai.preview.generative_models import GenerativeModel
# There isn't a direct "list_generative_models" easily accessible in the high-level SDK, 
# but we can try to list Model Garden models or just try to instantiate one and catch error.
# Alternatively, use the ModelServiceClient.

from google.cloud import aiplatform_v1

def list_foundation_models():
    client = aiplatform_v1.ModelServiceClient(
        client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
    )
    parent = f"projects/{project_id}/locations/{location}"
    # Note: Publisher models are under a different parent
    # projects/{project}/locations/{location}/publishers/{publisher}/models/{model}
    
    # Let's try to list publisher models
    parent = f"projects/{project_id}/locations/{location}/publishers/google"
    request = aiplatform_v1.ListPublishersRequest(parent=f"projects/{project_id}/locations/{location}")
    # Actually ListPublishers is not what we want. We want ListModels but for publishers.
    # It seems the SDK hides this a bit.
    
    # Let's try a simpler approach: Just print the error from a known valid call or use a known working one from docs.
    # But wait, the error 404 implies the resource path is wrong.
    
    print("Attempting to list publisher models...")
    # This is a bit hacky, but let's try to list models using the lower level API if possible.
    # Actually, let's just try to use the 'gemini-1.0-pro-001' which is a specific version.
    
    models = ["gemini-1.0-pro-001", "gemini-1.0-pro", "gemini-1.5-pro-001", "gemini-1.5-pro-preview-0409"]
    for m in models:
        try:
            model = GenerativeModel(m)
            print(f"Model {m} instantiated successfully (client side).")
        except Exception as e:
            print(f"Model {m} failed: {e}")

if __name__ == "__main__":
    list_foundation_models()
