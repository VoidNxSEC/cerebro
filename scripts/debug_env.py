import os
import sys

print("LD_LIBRARY_PATH:", os.environ.get("LD_LIBRARY_PATH"))
print("PATH:", os.environ.get("PATH"))

try:
    from langchain_google_vertexai import VertexAIEmbeddings
    print("Import Successful")
    emb = VertexAIEmbeddings(model="text-embedding-004")
    print("Init Successful")
except Exception as e:
    print("Error:", e)
