FROM chromadb/chroma:latest

EXPOSE 8000

CMD ["chromadb", "run", "--host", "0.0.0.0", "--port", "8000"]
