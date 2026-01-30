# Deployment Guide - AI Visa Eligibility Screening System

## Quick Start

### Prerequisites
- Python 3.10+
- Virtual environment (venv) already configured
- All required packages installed (see requirements.txt)

### Running the Application

```bash
# Navigate to project directory
cd /home/ushan/Visa

# Activate virtual environment
source venv/bin/activate

# Run the Streamlit application
streamlit run app.py
```

The application will be available at: `http://localhost:8501`

---

## System Requirements

### Minimum Specifications
- Python 3.10+
- 4GB RAM (8GB recommended)
- 1GB disk space
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Required Python Packages
See `requirements.txt` for complete dependency list. Key packages include:
- streamlit >= 1.0
- sentence-transformers
- faiss-cpu or faiss-gpu
- langchain
- openai (for LLM features)

### Optional Services
- FAISS vector database (for RAG retrieval)
- LLM API (for explanation generation)
- OpenAI API key (if using LLM explanations)

---

## Environment Configuration

### Environment Variables
Create a `.env` file or set these environment variables:

```bash
# For LLM features (optional)
export OPENAI_API_KEY="your-api-key-here"

# For RAG/vector database (if using cloud storage)
export PINECONE_API_KEY="your-pinecone-key"  # Optional
export FAISS_INDEX_PATH="./vector_db/index.faiss"
```

### Database Configuration
- FAISS index location: `./vector_db/index.faiss`
- Policy documents storage: `./data/`
- Vector embeddings: Embedded in FAISS index

---

## Application Features

### Visa Categories Supported
1. **Graduate Visa** - For UK degree completion
2. **Student Visa** - For UK education
3. **Skilled Worker Visa** - For employment
4. **Health and Care Worker Visa** - For healthcare roles
5. **Standard Visitor Visa** - For tourism/visits

### Core Functionality
- Multi-step eligibility assessment (4 steps)
- AI-powered policy evaluation
- Confidence scoring and breakdowns
- Rule-based eligibility determination
- Optional LLM explanations
- Policy citation retrieval

### User Flow
1. **Step 1:** Select visa category
2. **Step 2:** Enter basic applicant information
3. **Step 3:** Provide visa-specific details
4. **Step 4:** Review eligibility results and confidence scores

---

## Styling & Customization

### Current Theme
- **Color Scheme:** Black and white professional theme
- **Accent:** White on black backgrounds
- **Style:** Flat design, no rounded corners or gradients
- **Font:** System default (professional sans-serif)

### Modifying Colors
All colors are defined in the CSS style block at the beginning of `app.py`. 
To modify colors, update the CSS variables in the `<style>` section:

```python
st.markdown("""
<style>
    /* Change colors here */
    :root {
        --primary: #000000;        /* Black background */
        --accent: #FFFFFF;         /* White text */
        --muted: #B0B0B0;         /* Gray text */
        --background: #000000;     /* Page background */
        --border: #2A2A2A;        /* Border color */
    }
</style>
""", unsafe_allow_html=True)
```

### Responsive Design
The application is fully responsive and adapts to:
- Mobile devices (tested on 375px+ width)
- Tablets (768px+ width)
- Desktop screens (1920px+ width)

---

## Performance Optimization

### Caching
The application uses Streamlit's caching for:
- RAG system initialization
- Vector database loading
- LLM model loading
- Calculations and heavy computations

### Tips for Better Performance
1. Use a GPU if available (FAISS-GPU recommended)
2. Pre-load vector databases on startup
3. Cache LLM models locally
4. Consider using a cloud deployment (Streamlit Cloud, AWS, GCP)

### Typical Response Times
- Visa selection: < 1 second
- Form submission: < 2 seconds
- Eligibility evaluation: 1-3 seconds (depends on LLM)
- Policy retrieval: < 1 second

---

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Verify Python version
python3 --version  # Should be 3.10+

# Reinstall dependencies
pip install -r requirements.txt

# Clear Streamlit cache
streamlit cache clear
```

#### Missing Module Errors
```bash
# Ensure correct imports
# Should use: visa_rules and visa_services
# NOT: rules and services

# Activate virtual environment
source venv/bin/activate

# Install missing packages
pip install -r requirements.txt
```

#### FAISS Index Not Found
```bash
# Ensure vector database exists
ls -la vector_db/index.faiss

# If missing, you'll need to rebuild the index
# Contact system administrator for database files
```

#### LLM API Errors
- Check OpenAI API key is valid
- Verify API quota and billing
- Check network connectivity
- Review error logs in Streamlit terminal

### Logging & Debugging
Enable verbose output:
```bash
streamlit run app.py --logger.level=debug
```

---

## Production Deployment

### Recommended Deployment Options

#### 1. Streamlit Cloud
```bash
# Push to GitHub, then deploy via Streamlit Cloud
# Free tier available with limitations
```

#### 2. Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### 3. Cloud Platforms
- **AWS:** EC2 + Load Balancer
- **Google Cloud:** Cloud Run
- **Microsoft Azure:** Container Instances
- **DigitalOcean:** App Platform

### Performance Tuning for Production
- Use production-grade web server (e.g., Gunicorn)
- Enable caching and CDN for static assets
- Use load balancing for multiple instances
- Monitor memory and CPU usage
- Set up logging and error tracking

---

## Security Considerations

### API Keys & Secrets
- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate keys regularly
- Use secrets management (AWS Secrets Manager, Azure Key Vault)

### Data Privacy
- Users input is processed locally
- No data is stored after session ends
- FAISS vector database is read-only
- Compliance with data protection regulations

### Deployment Security
- Use HTTPS for all connections
- Implement rate limiting
- Add authentication if needed
- Regular security updates
- Monitor for suspicious activity

---

## Support & Maintenance

### Regular Maintenance Tasks
- Weekly: Check application logs
- Monthly: Update vector database if needed
- Monthly: Verify API quotas and usage
- Quarterly: Update Python packages
- Quarterly: Review and update policies

### Monitoring
Set up monitoring for:
- Application uptime
- Response times
- Error rates
- Resource usage
- API quota usage

### Getting Help
1. Check logs: `streamlit run app.py --logger.level=debug`
2. Review error messages in terminal
3. Check documentation files
4. Review REFACTORING_SUMMARY.md for changes

---

## Additional Resources

### Documentation Files
- `README.md` - Project overview
- `REFACTORING_SUMMARY.md` - Detailed refactoring changes
- `requirements.txt` - Python dependencies

### External Resources
- [Streamlit Documentation](https://docs.streamlit.io/)
- [UK Visa Information](https://www.gov.uk/check-uk-visa)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [LangChain Documentation](https://docs.langchain.com/)

---

## Version Information

- **Application Name:** AI Visa Eligibility Screening System
- **Version:** 1.0 (Post-Refactoring)
- **Python Version:** 3.10+
- **Streamlit Version:** Latest
- **Last Updated:** January 26, 2026
- **Owner:** Srijan

---

**This application is for informational purposes only and does not constitute legal advice.**
