# Evaluator - Educational Credential Analysis System

A modular Python system for extracting educational credentials from Salesforce, normalizing the data into SQLite, performing automated credential analysis on PDF documents using Large Language Models with tool calling capabilities, and generating professional PDF evaluation reports.

## Quick Setup

### Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
Create `.env` file with your credentials:
```env
# Salesforce Configuration
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token
SALESFORCE_CONSUMER_KEY=your_consumer_key
SALESFORCE_CONSUMER_SECRET=your_consumer_secret

# LLM Configuration - Choose Provider
LLM_PROVIDER=anthropic                   # Options: anthropic, gemini

# Anthropic Configuration
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_MODEL=claude-sonnet-4-20250514
ANTHROPIC_TIMEOUT=1200.0

# Gemini Configuration  
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.1
```

## Usage

### Command Line Interface
```bash
# Database Operations
python main.py migrate                    # Extract from Salesforce → Load to SQLite
python main.py reset                      # Drop and recreate all database tables
python main.py stats                      # Display database statistics and integrity

# Credential Analysis
python main.py analyze "filename.pdf" --type general    # Analyze PDF (general evaluation)
python main.py analyze "filename.pdf" --type cbc        # Analyze PDF (course-by-course)

# PDF Report Generation
# The analyze command automatically generates a PDF evaluation report
# Output: results/filename_evaluation_report.pdf
```

### Command Details

| Command | Description | Output |
|---------|-------------|--------|
| `migrate` | Extracts data from Salesforce `Credentials_Form_Setup_Data__c` object and loads into normalized SQLite tables | Console log + `data/evaluator.db` |
| `reset` | Drops all tables and recreates schema (destructive) | Clean database |
| `stats` | Shows record counts and data integrity status | Console statistics |
| `analyze <filename> [--type general\|cbc]` | Processes PDF using LLM + database tools (default: general) | Console output + timestamped JSON + PDF report in `results/` |

### Analysis Output
- **Console**: Human-readable credential analysis with validation status
- **JSON**: Comprehensive results with metadata in `results/YYYYMMDD_HHMMSS_filename.json`
- **PDF Report**: Professional evaluation report in `results/filename_evaluation_report.pdf`

## System Architecture

```mermaid
graph TD
    A[PDF Document] --> B[DocumentProcessor]
    B --> C{LLM Provider}
    C -->|anthropic| D[AnthropicService]
    C -->|gemini| E[GeminiService]
    D --> F[LLM Analysis with Tools]
    E --> F
    F --> G{Tool Calls}
    
    G --> H[search_countries]
    G --> I[find_institutions] 
    G --> J[get_foreign_credentials]
    G --> K[get_program_lengths]
    
    H --> L[(SQLite Database)]
    I --> L
    J --> L
    K --> L
    
    L --> M[Tool Results]
    M --> F
    
    F --> N[Structured Analysis]
    N --> O[JSON Output]
    N --> P[Console Display]
    N --> S[PDF Generator]
    S --> T[PDF Report]
    
    U[Salesforce API] --> V[Data Migration]
    V --> W[Schema Normalization]
    W --> L
    
    R[config.py] --> C
    R --> V
```

## Project Structure

```
Evaluator/
├── config.py                           # Environment variables & credentials
├── main.py                             # CLI entry point & orchestration
├── requirements.txt                    # Python dependencies
│
├── data/                               # Database storage
│   └── evaluator.db                   # SQLite database (generated)
│
├── results/                            # Analysis output
│   └── YYYYMMDD_HHMMSS_filename.json  # Timestamped results
│
├── database/                           # Database layer
│   ├── connection.py                  # SQLite connection management
│   ├── schema.py                      # Table definitions (7 tables)
│   ├── migrations.py                  # Salesforce → SQLite ETL
│   └── queries.py                     # Database query utilities
│
├── salesforce/                         # Salesforce integration
│   ├── client.py                      # Authentication & connection
│   └── extractors.py                  # SOQL queries & data extraction
│
├── llm_services/                       # LLM abstraction layer
│   ├── __init__.py                    # Provider factory & service creation
│   ├── base.py                        # Abstract base class
│   ├── anthropic/                     # Anthropic Claude integration
│   │   ├── __init__.py               # Anthropic service exports
│   │   ├── anthropic_service.py      # Claude service implementation
│   │   └── tools.py                  # Anthropic tool schemas
│   └── gemini/                        # Google Gemini integration
│       ├── __init__.py               # Gemini service exports
│       ├── gemini_service.py         # Gemini service implementation
│       └── tools.py                  # Gemini function declarations
│
├── document_processor/                 # PDF analysis orchestration
│   ├── processor.py                   # Main processing pipeline
│   ├── models.py                      # Result data structures
│   ├── pdf_adapter.py                 # Converts analysis to PDF format
│   └── pdf_service.py                 # PDF generation service
│
├── pdf_generator/                      # PDF report generation
│   ├── pdf_generator.py               # Main PDF generation class
│   ├── __init__.py                    # Package exports
│   ├── config/                        # PDF configuration
│   │   └── pdf_config.py             # Layout, fonts, spacing settings
│   ├── core/                          # Core PDF components
│   │   ├── pdf_document.py           # Document management
│   │   ├── font_manager.py           # Font handling
│   │   └── image_manager.py          # Image/background handling
│   ├── types/                         # PDF data types
│   │   └── pdf_types.py              # Pydantic models for PDF data
│   └── utils/                         # PDF utilities
│       └── text_utils.py             # Text processing, wrapping
│
├── prompts/                            # LLM prompts by provider
│   ├── anthropic/                     # Anthropic Claude prompts
│   │   ├── general_instructions.py   # General analysis instructions
│   │   └── cbc_instructions.py       # Course-by-course instructions
│   └── gemini/                        # Google Gemini prompts
│       ├── general_instructions.py   # General analysis instructions
│       ├── cbc_instructions.py       # Course-by-course instructions
│       └── system_instruction.py     # System-level role and behavior
│
├── public/                             # Static resources
│   └── resources/
│       ├── background.png            # PDF background template
│       ├── signature.png             # Signature image
│       └── fonts/                    # Font files (Arial variants)
│
└── utils/                              # Shared utilities
    └── helpers.py                     # Logging, validation, formatters
```

## Database Schema

### Normalized Design
- **Natural Key**: `country_name` as TEXT PRIMARY KEY
- **UUID Keys**: All other tables use UUID4 as TEXT PRIMARY KEY
- **Foreign Keys**: Direct text-based references to country_name

### Tables (7)
1. **`country`** - Master reference table
2. **`foreign_credential`** - Credential types by country
3. **`institution`** - Educational institutions by country
4. **`program_length`** - Program durations by country
5. **`grade_scale`** - Grading systems by country
6. **`us_equivalency`** - US degree equivalencies (standalone)
7. **`notes`** - General notes (standalone)

### Data Source
All tables populated from Salesforce `Credentials_Form_Setup_Data__c` where:
- `Type__c` field determines target table
- `Key__c` contains country name (natural key)
- `Value_1__c` through `Value_5__c` contain typed data

## Implementation Details

### LLM Integration
- **Providers**: Anthropic Claude & Google Gemini (extensible architecture)
- **Provider Selection**: Set via `LLM_PROVIDER` environment variable
- **Tool Calling**: 6 database tools available to all LLMs
- **Context**: Base64 PDF upload + structured prompt
- **Timeout**: 20-minute limit for large documents (Anthropic)
- **Tracking**: Complete conversation metadata with token usage

#### Anthropic Claude Service
- **Manual Tool Calling**: Full control over function execution cycle
- **Iterative Process**: Model → Tool Call → Execution → Result → Model
- **Conversation Management**: Manual tracking of multi-turn interactions
- **Token Tracking**: Detailed input/output token usage monitoring

#### Google Gemini Service  
- **Manual Function Calling**: Full control over function execution cycle (AFC disabled)
- **Iterative Process**: Model → Function Call → Execution → Result → Model (same as Anthropic)
- **Conversation Management**: Manual tracking of multi-turn interactions
- **Token Tracking**: Detailed input/output token usage monitoring
- **Tool Call Tracking**: Complete audit trail of function calls with parameters, results, and timing
- **Why Manual over AFC**: Provides detailed tracking and monitoring required for analysis transparency

### Available Tools for LLM
1. **`search_countries(query)`** - Fuzzy country name matching
2. **`find_institutions(country_name, query)`** - Institution search within country
3. **`get_foreign_credentials(country_name)`** - Available credential types
4. **`get_program_lengths(country_name)`** - Typical program durations
5. **`get_grade_scales(country_name)`** - Grading systems by country
6. **`get_us_equivalencies()`** - All US degree equivalencies and descriptions

### Data Flow
1. **PDF Upload** → Base64 encoding → Claude API
2. **LLM Analysis** → Tool calls → Database queries → Results aggregation
3. **Output Generation** → Structured JSON + Human-readable console
4. **Metadata Capture** → Tool calls, token usage, timing, parameters

### Key Features
- **Modular Architecture**: Separated concerns (DB, Salesforce, LLM, Processing, PDF Generation)
- **Comprehensive Logging**: DEBUG/INFO levels with structured output
- **Error Handling**: Graceful failures with detailed error reporting
- **Extensible**: Abstract base classes for multiple LLM providers
- **Production Ready**: Robust connection management, retry logic, validation
- **Professional PDF Reports**: Automated generation of formatted evaluation reports

## PDF Report Generation

### Features
- **Automatic Generation**: PDF reports are created automatically after each credential analysis


### Report Sections
1. **Header**: Date, case number, student information, evaluation type
2. **Credentials Summary**: Highlighted box with US equivalency statement
3. **Credential Details**: Varies by evaluation type
   - **General Evaluations**: Country, institution, foreign credential, program of study, attendance dates, program length, and US equivalency for each credential
   - **Course-by-Course (CBC) Evaluations**: Same as general plus detailed course analysis section with grade conversion tables for each credential
4. **Comments**: NACES membership notice and authentication requirements
5. **Policy Statements**: Comprehensive evaluation policies and grade conversion information

#### Credential Details Format
- **Institution Names**: Foreign name on first line, English translation on second line (when available)
- **Foreign Credentials**: Foreign credential type on first line, English translation on second line (when available)
- **Course Analysis** (CBC only): Individual course listings with grades, credit hours, and US equivalents in tabular format

### PDF Technical Details
- **Engine**: ReportLab for PDF generation
- **Fonts**: Arial family with bold and italic variants
- **Background**: Custom SpanTran template with watermark
- **Page Size**: Standard US Letter (8.5" x 11")
- **Margins**: Consistent margins with proper text boundaries

## Technical Specifications

### Dependencies
- **Core**: `simple-salesforce`, `anthropic`, `google-genai`
- **Database**: SQLite (built-in)
- **PDF Generation**: `reportlab`, `pypdf`, `Pillow`
- **Data Models**: `pydantic`
- **Utilities**: `python-dotenv`, `pathlib`


### Monitoring
- **Token Tracking**: Input/output tokens per interaction
- **Tool Metrics**: Execution time, success/failure rates
- **Conversation Flow**: Complete audit trail of LLM interactions

## Development

### Adding LLM Providers
1. Create new provider folder in `llm_services/`
2. Extend `BaseLLMService` with provider-specific implementation
3. Implement required methods: `analyze_pdf_document()`, `get_model_info()`
4. Add provider to `create_llm_service()` factory in `llm_services/__init__.py`
5. Add provider-specific configuration to `config.py`
6. Add provider-specific prompts in `prompts/`

### Adding Database Tools
1. Add method to `DatabaseTools` class in `llm_services/tools.py`
2. Define schema in `TOOL_SCHEMAS`
3. Update `tool_map` in `execute_tool()`
4. Update prompt documentation

### Database Schema Changes
1. Modify table definitions in `database/schema.py`
2. Update migration logic in `database/migrations.py`
3. Add queries to `database/queries.py`
4. Update project structure documentation

## Data Model Architecture

### Overview
The `document_processor/models.py` file defines the complete data structure for credential analysis results. It serves as the bridge between LLM JSON output and PDF generation, ensuring type safety and consistent data flow throughout the system.

### Core Components

#### Data Classes
- **`CredentialAnalysisResult`**: Top-level container for complete analysis
- **`CredentialInfo`**: Individual credential with all associated data
- **`CountryMatch`**, **`InstitutionMatch`**, **`CredentialMatch`**: Database validation results
- **`AttendanceDates`**, **`ProgramLength`**, **`GradeScaleInfo`**, **`USEquivalency`**: Supporting credential details

#### Builder Pattern
- **`CredentialAnalysisResultBuilder`**: Converts LLM JSON responses to structured objects
- **`from_llm_response()`**: Parses and validates incoming JSON
- **`to_dict()`**: Serializes results for JSON storage

### Adding New LLM Outputs

When extending the system with new data fields, follow this complete workflow:

#### 1. Update LLM Prompts
```python
# In prompts/anthropic/general_instructions.py and other prompt files
"new_field": {
  "extracted_value": "string (from document)", 
  "validated_value": "string (from database)",
  "confidence": "high/medium/low"
}
```

#### 2. Extend Data Models
```python
# In document_processor/models.py
@dataclass 
class NewDataType:
    extracted_value: Optional[str] = None
    validated_value: Optional[str] = None
    confidence: str = "not_found"

# Add to CredentialInfo
@dataclass
class CredentialInfo:
    # ... existing fields ...
    new_field: Optional[NewDataType] = None
```

#### 3. Update Builder Logic
```python
# In CredentialAnalysisResultBuilder.from_llm_response()
new_data = cred_data.get("new_field", {})
new_field = NewDataType(
    extracted_value=new_data.get("extracted_value"),
    validated_value=new_data.get("validated_value"), 
    confidence=new_data.get("confidence", "not_found")
) if new_data else None

# Add to CredentialInfo constructor
credential = CredentialInfo(
    # ... existing fields ...
    new_field=new_field
)
```

#### 4. Update JSON Serialization
```python
# In CredentialAnalysisResultBuilder.to_dict()
"new_field": {
    "extracted_value": cred.new_field.extracted_value,
    "validated_value": cred.new_field.validated_value,
    "confidence": cred.new_field.confidence
} if cred.new_field else None
```

#### 5. Extend PDF Adapter
```python
# In document_processor/pdf_adapter.py
# Extract new field for PDF generation
new_field_value = ""
if cred.new_field and cred.new_field.validated_value:
    new_field_value = cred.new_field.validated_value
elif cred.new_field and cred.new_field.extracted_value:
    new_field_value = cred.new_field.extracted_value

# Add to CredentialGroup creation
credential_group = CredentialGroup(
    # ... existing fields ...
    newField=new_field_value  # Note: camelCase for PDF types
)
```

#### 6. Update PDF Types
```python
# In pdf_generator/types/pdf_types.py
@dataclass
class CredentialGroup:
    # ... existing fields ...
    newField: str = ""
```

#### 7. Update PDF Generator
```python
# In pdf_generator/pdf_generator.py
def _draw_credential_details(self, credential: CredentialGroup, start_y: float):
    # ... existing drawing code ...
    
    # Draw new field
    if credential.newField:
        current_y = self._draw_labeled_text(
            "New Field:", 
            credential.newField,
            current_y - 15
        )
```

#### 8. Update Console Display
```python
# In main.py analyze_folio function
if cred.new_field and cred.new_field.validated_value:
    status = "[MATCH]" if cred.new_field.confidence in ['high', 'medium'] else "[NO MATCH]"
    print(f"{status} New Field: '{cred.new_field.extracted_value}' → '{cred.new_field.validated_value}' ({cred.new_field.confidence})")
```

### Data Flow Summary
```
LLM JSON → Builder.from_llm_response() → CredentialInfo → PDF Adapter → PDF Types → PDF Generator → Visual Output
         ↓
    Builder.to_dict() → JSON Storage
         ↓  
    Console Display → Human-readable output
```

This architecture ensures that all new data fields flow consistently through the entire system while maintaining type safety and validation at each step.

## Recent Updates

### August 2025
- **Multi-Provider Support**: Added Google Gemini as alternative to Anthropic Claude
- **LLM Service Restructure**: Organized providers into separate modules with shared base class
- **Automatic Function Calling**: Gemini integration with AFC for streamlined tool execution
- **Provider Switching**: Dynamic LLM provider selection via environment variable
- ** Tool Set**: Added grade scales tool for more comprehensive credential analysis
- **Database Lookup Pattern**: Implemented validated_id workflow for foreign credentials and grade scales to prevent LLM from making up values not in the database

### Database Lookup Workflow Pattern
To prevent the LLM from generating values not present in the database, the system now uses a **validated_id workflow** for critical fields:

1. **LLM Returns Only IDs**: Instead of returning validated text values, the LLM returns only the `validated_id` (UUID) from database searches
2. **PDF Generator Does Database Lookup**: The PDF generator queries the database using the UUID to retrieve the actual display values
3. **Fallback to Extracted Values**: If no validated_id is provided or database lookup fails, the system falls back to the extracted text from the document

**Fields Currently Using This Pattern:**
- **Foreign Credentials**: `validated_credential.id` → Database lookup for `foreign_credential` and `english_credential`
- **Grade Scales**: `validated_scale.id` → Database lookup for `bifurcation_setup` and grade conversion tables

**Benefits:**
- **Data Integrity**: Ensures only values actually in the database appear in final reports
- **Consistency**: Eliminates LLM-generated variations of the same database values
- **Maintainability**: Centralizes display logic in the PDF generator rather than LLM prompts

**Future Implementation:**
Consider converting other fields (institutions, program lengths, US equivalencies) to use this same pattern to further improve data integrity and prevent LLM-generated values from appearing in evaluation reports.



## TODO - Future Improvements

### Data Validation & Security
- **LLM Output Validation**: Currently the system trusts the LLM to accurately populate `validated_name`/`validated_type` fields from database tool responses. There's no technical enforcement preventing the LLM from fabricating values that end up on the PDF. Need to implement cross-reference validation between LLM output and actual tool call responses within conversation metadata to ensure database integrity.