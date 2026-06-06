# UK Visa Eligibility Checker

A professional Streamlit-based decision support system for UK visa eligibility screening. The application combines structured route-specific rules with retrieval-augmented generation to help users review eligibility requirements, identify missing information, and generate detailed assessment outputs.

Live deployment: [http://13.214.214.83:8501/](http://13.214.214.83:8501/)

## Overview

The system is designed for preliminary UK visa eligibility assessment across common immigration routes. It collects applicant details, applies route-specific validation logic, retrieves relevant policy context, and can generate an AI-assisted explanation using the configured local or API-compatible LLM service.

This tool is intended for decision support and document preparation guidance. It does not replace official Home Office guidance or qualified immigration advice.

## Supported Visa Routes

- Student Visa
- Skilled Worker Visa
- Graduate Visa
- Health and Care Worker Visa
- Standard Visitor Visa

## Key Features

- Multi-step applicant intake and eligibility assessment
- Visa-route-specific rules and validation logic
- Retrieval-augmented policy support using local vector indexes and optional Pinecone integration
- LLM-assisted explanation generation through Ollama, LM Studio, or an OpenAI-compatible endpoint
- Downloadable assessment reports
- Professional Streamlit interface with a black-and-white visual theme
- Docker-ready deployment configuration
- AWS-hosted Streamlit deployment

## Technology Stack

| Layer | Technology |
| --- | --- |
| Application | Python, Streamlit |
| Rule engine | Custom Python modules in `visa_rules/` |
| Services | Custom service layer in `visa_services/` |
| RAG orchestration | LangChain, Chroma, Pinecone, FAISS |
| Embeddings | HuggingFace Sentence Transformers |
| LLM runtime | Ollama, LM Studio, or OpenAI-compatible API |
| Deployment | Docker, AWS EC2 |

## Project Structure

```text
.
+-- app.py                  # Streamlit application entrypoint and UI orchestration
+-- backend/                # RAG ingestion and retrieval implementations
+-- visa_rules/             # Visa-specific eligibility rule logic
+-- visa_services/          # Supporting services for validation and LLM explanations
+-- vector_db/              # Local vector database artifacts
+-- uk_visa_db/             # UK visa policy database artifacts
+-- visa_db/                # Additional visa database artifacts
+-- Dockerfile              # Container image definition
+-- requirements.txt        # Python dependencies
+-- .env.example            # Environment variable template
`-- DEPLOYMENT_GUIDE.md     # Additional operational notes
```

## Prerequisites

- Python 3.10 or later
- `pip` and `venv`
- Docker, if running with containers
- Pinecone API key, if using Pinecone-backed retrieval
- Local or remote LLM endpoint, depending on your configuration
- AWS EC2 instance, security group, and public IP for cloud deployment

## Environment Configuration

Create a local `.env` file from the example template:

```bash
cp .env.example .env
```

Update the values for your environment:

```env
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=visa-index

UK_VISA_DB_PATH=./uk_visa_db
INDIA_VISA_DB_PATH=./visa_db

OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama2

LLM_BASE_URL=http://localhost:1234/v1
MODEL_NAME=google/gemma-4-e4b
LLM_API_KEY=lm-studio

LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model
```

Do not commit real API keys, credentials, or private endpoint values.

## Local Installation

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd Visa
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Start the application:

```bash
streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

## Docker Usage

Build the Docker image:

```bash
docker build -t uk-visa-eligibility-checker .
```

Run the container:

```bash
docker run --env-file .env -p 8501:8501 uk-visa-eligibility-checker
```

Open the application:

```text
http://localhost:8501
```

The Docker image uses Python 3.10, installs the required system packages, exposes port `8501`, and includes a Streamlit health check at:

```text
http://localhost:8501/_stcore/health
```

## AWS Deployment

The application has been deployed on AWS and is currently accessible at:

```text
http://13.214.214.83:8501/
```

### Recommended AWS Architecture

- AWS EC2 instance running Linux
- Docker-based application runtime
- Security group allowing inbound TCP traffic on port `8501`
- Environment variables stored outside version control
- Optional reverse proxy such as Nginx for HTTPS, domain routing, and request handling
- Optional process manager or Docker restart policy for automatic recovery

### EC2 Deployment Steps

1. Launch an EC2 instance with sufficient memory for Streamlit, embeddings, and vector search.
2. Configure the security group to allow inbound traffic on port `8501`.
3. Install Docker on the EC2 instance.
4. Clone this repository onto the instance.
5. Create the `.env` file using `.env.example` as the template.
6. Build the Docker image:

```bash
docker build -t uk-visa-eligibility-checker .
```

7. Run the container:

```bash
docker run -d \
  --name uk-visa-app \
  --env-file .env \
  -p 8501:8501 \
  --restart unless-stopped \
  uk-visa-eligibility-checker
```

8. Verify the application health:

```bash
curl http://localhost:8501/_stcore/health
```

9. Open the public AWS URL:

```text
http://13.214.214.83:8501/
```

### Updating the AWS Deployment

Pull the latest code, rebuild the image, and recreate the container:

```bash
git pull
docker build -t uk-visa-eligibility-checker .
docker stop uk-visa-app
docker rm uk-visa-app
docker run -d \
  --name uk-visa-app \
  --env-file .env \
  -p 8501:8501 \
  --restart unless-stopped \
  uk-visa-eligibility-checker
```

## Operational Notes

- Streamlit runs on port `8501`.
- The application depends on local data directories such as `vector_db/`, `uk_visa_db/`, and `visa_db/`.
- Large vector database artifacts should be handled carefully and should not be modified unless the retrieval index is being rebuilt intentionally.
- Local LLM services such as Ollama or LM Studio must be reachable from the runtime environment.
- If the app is deployed on EC2 and the LLM runs outside the container, configure the endpoint so the container can access it.

## Security Considerations

- Keep `.env` out of version control.
- Store production secrets in AWS Secrets Manager, EC2 environment configuration, or another managed secret store.
- Use HTTPS in production by placing Nginx, an Application Load Balancer, or another TLS termination layer in front of Streamlit.
- Restrict AWS security group rules to the minimum required ports and source ranges.
- Rotate API keys regularly.
- Do not expose local-only LLM or database services publicly unless they are protected.

## Troubleshooting

### Application does not start

Check the container logs:

```bash
docker logs uk-visa-app
```

Confirm that dependencies were installed successfully and that `app.py` is present in the image.

### Public URL is not reachable

Verify the EC2 security group allows inbound traffic on port `8501`, and confirm the container is running:

```bash
docker ps
```

### Health check fails

Run:

```bash
curl http://localhost:8501/_stcore/health
```

If the command fails, inspect Streamlit logs and confirm that the application is bound to `0.0.0.0`.

### LLM explanation is unavailable

Check that the configured `OLLAMA_URL`, `LLM_BASE_URL`, or LM Studio endpoint is reachable from the application environment. If the LLM is running on the EC2 host and the app runs in Docker, ensure the container can resolve and reach the host service.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
