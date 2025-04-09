# Smart Notes API
A modern notes application with vector search, intelligent tagging, and RAG capabilities.
## Features
- Create, read, update, and delete notes
- Automatic structure extraction from notes
- Intelligent tag suggestion
- Tag similarity matching
- Vector search for semantic retrieval
- Question answering with RAG (Retrieval-Augmented Generation)

## Architecture
The application is built using:
- FastAPI - Web framework
- Haystack - Vector search and RAG pipelines. Easy to manage pipelines with many tools.
- Qdrant - Vector database. Qdrant can efficiently handle large volumes of vectors.
- MongoDB - Document storage. Saving documents with different structure.
- OpenAI

## Architecture Diagrams and Videos

### System Architecture
![Architecture Overview](assets/architecture_overview.png)

### Note Processing Pipeline
![Note Processor](assets/note_processor.png)

### Demo Videos
1. **System Overview** - A walkthrough of the Smart Notes API capabilities and architecture
   - [Watch Video](https://example.com/smart-notes-overview)

2. **Vector Search Demo** - Demonstration of semantic search capabilities
   - [Watch Video](https://example.com/vector-search-demo)

3. **RAG Question Answering** - How the system leverages documents to answer questions
   - [Watch Video](https://example.com/rag-qa-demo)

## Project Structure
```
smart_notes_api/
├── app/
│   ├── **init**.py
│   ├── main.py                  # FastAPI application entry point
│   ├── models/                  # Data models
│   ├── storage/                 # Storage implementations
│   ├── search/                  # Vector search
│   ├── processing/              # Note processing pipelines
│   ├── api/                     # API routes
│   └── config.py                # Configuration
├── requirements.txt
├── Dockerfile
├── docker-compose
└── README.md
```
## Setup
### Environment Variables
```
# Storage configuration
STORAGE_TYPE=memory  # memory or mongodb
MONGODB_URI=mongodb://localhost:27017
DB_NAME=smart_notes
# Qdrant configuration
USE_IN_MEMORY_QDRANT=true
QDRANT_HOST=localhost
QDRANT_PORT=6333
# OpenAI API key for LLM features
OPENAI_API_KEY=your-api-key
# Logging and debug
LOG_LEVEL=INFO
DEBUG=false
```
### Running Locally
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables (create a `.env` file)
4. Run the application: `uvicorn src.main:app --reload`
### Using Docker Compose
```bash
docker-compose up -d
```
## API Endpoints
### Notes
- `POST /notes` - Create a new note
- `GET /notes/{note_id}` - Get a specific note
- `PUT /notes/{note_id}` - Update a note
- `DELETE /notes/{note_id}` - Delete a note
- `GET /notes` - List recent notes
### Search
- `POST /search/vector` - Search notes using vector similarity
- `POST /search/tags` - Search notes by tags
- `GET /search/tags` - Get all tags
### Tags
- `GET /tags` - Get all tags
- `POST /tags/process` - Process a tag through the tag vector store
### Question Answering
- `POST /qa` - Answer a question using RAG
### System
- `GET /health` - Health check
- `GET /status` - System status and component information
## Scalability Options
### Database Scaling
- MongoDB: Sharded clusters for horizontal scaling
- Implement caching for frequently accessed notes
### Vector Search Scaling
- Use full Qdrant deployment with clustering instead of in-memory storage
- Implement vector database sharding for distributed search
- Utilize sparse vector search to filter part of the values with dense search
### LLM Optimization
- Use smaller, local LLMs instead of OpenAI where applicable
