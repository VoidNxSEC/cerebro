# scripts/03_generate_embeddings.py
"""
Generate embeddings using GCP Vertex AI.
Optimized batch processing for efficient credit usage.
"""

try:
    from google.cloud import discoveryengine_v1beta as discoveryengine
    from google.cloud import aiplatform
    from google.api_core.client_options import ClientOptions
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

from typing import List, Dict
import json
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]

class VertexEmbeddingGenerator:
    """Generate high-quality embeddings using Vertex AI."""

    def __init__(self, project_id: str, location: str = "us-central1"):
        if not GCP_AVAILABLE:
            raise ImportError("google-cloud-aiplatform is required for embedding generation")
        aiplatform.init(project=project_id, location=location)
        self.model_name = "text-embedding-004"
        self.batch_size = 250  # Vertex AI limit

    def generate_embeddings(self, artifacts: List[Dict]) -> List[Dict]:
        """Generate embeddings for all artifacts."""

        print(f"🚀 Generating embeddings for {len(artifacts)} artifacts using Vertex AI")
        print(f"💰 This will use your GCP credits efficiently!")

        results = []

        # Process in batches
        for i in tqdm(range(0, len(artifacts), self.batch_size)):
            batch = artifacts[i:i + self.batch_size]

            # Prepare texts for embedding
            texts = [self.prepare_text(artifact) for artifact in batch]

            # Call Vertex AI
            embeddings = self.batch_embed(texts)

            # Combine with artifacts
            for artifact, embedding in zip(batch, embeddings):
                results.append({
                    **artifact,
                    'embedding': embedding,
                    'embedding_model': self.model_name,
                })

        return results

    def prepare_text(self, artifact: Dict) -> str:
        """
        Prepare optimized text for embedding.
        Combines: name + docstring + context + metadata.
        """
        parts = [
            f"Repository: {artifact['repo']}",
            f"Type: {artifact['artifact_type']}",
            f"Name: {artifact['name']}",
        ]

        if artifact['documentation']:
            parts.append(f"Documentation: {artifact['documentation']}")

        parts.append(f"Content:\n{artifact['content']}")

        if artifact['dependencies']:
            parts.append(f"Dependencies: {', '.join(artifact['dependencies'])}")

        return "\n\n".join(parts)

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """Call Vertex AI batch embedding API."""

        # Vertex AI Embeddings API
        from vertexai.preview.language_models import TextEmbeddingModel

        model = TextEmbeddingModel.from_pretrained("text-embedding-004")

        embeddings = model.get_embeddings(texts)

        return [emb.values for emb in embeddings]

def main():
    import os

    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("Set GCP_PROJECT_ID environment variable")

    # Load analyzed artifacts
    artifacts_path = Path("./data/analyzed/all_artifacts.json")
    with open(artifacts_path) as f:
        artifacts = json.load(f)

    print(f"📚 Loaded {len(artifacts)} artifacts")

    # Generate embeddings
    generator = VertexEmbeddingGenerator(project_id)
    embedded_artifacts = generator.generate_embeddings(artifacts)

    # Save results
    output_path = Path("./data/embeddings/artifacts_embedded.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(embedded_artifacts, f)

    print(f"✅ Saved embeddings to {output_path}")
    print(f"💾 Total size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()
