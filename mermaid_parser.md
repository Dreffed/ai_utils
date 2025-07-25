# Mermaid to Miro/Lucid Converter Application
# Directory structure:
mermaid_parser/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── mermaid_parser.py      # Mermaid parsing logic
├── converters/            # Platform-specific converters
│   ├── __init__.py
│   ├── miro_converter.py
│   └── base_converter.py
├── static/                # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── templates/             # HTML templates
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker compose for easy deployment
└── README.md
