"""
Course Extraction Instructions

Modular prompt for extracting course information from academic transcripts.
This prompt is injected into CBC analysis instructions.
"""

COURSE_EXTRACTION_INSTRUCTIONS = """
**COURSE EXTRACTION SECTION:**

Extract course names from the English translations of the documents found in the pdf (you do not need translate yourself, translations are given). Focus on:

1. **Section Headers**: Academic periods (e.g., "ACADEMIC YEAR 1992 SEMESTER 1", "Fall 2020", "Term I")
2. **Course Names**: Extract only the English course/subject names from the English translation

**Course Extraction Rules:**
- ONLY extract course names from English translation sections (English translations are always present)
- Extract subjects in Title Case
- Preserve exact section header text as it appears
- Use ONLY the English course names - ignore original foreign language course names
- Maintain document order exactly - do not reorder sections or courses
- Include courses even if they appear without grades or credits
- Do NOT extract foreign credits, foreign grades, or any numerical data
- Focus only on the descriptive course titles/names

**Course JSON Structure:**
For each credential, add a "course_analysis" section containing only course names:

```json
"course_analysis": {
  "sections": [
    {
      "section_name": "ACADEMIC YEAR 1992 SEMESTER 1",
      "courses": [
        {
          "subject": "Communication and Language"
        },
        {
          "subject": "Study and Understanding of Man"
        }
      ]
    },
    {
      "section_name": "ACADEMIC YEAR 1993 SEMESTER 1", 
      "courses": [
        {
          "subject": "General Pedagogy"
        }
      ]
    }
  ]
}
```

**Important Notes:**
- Only extract courses that clearly belong to the current credential being analyzed
- Use English translation course names exclusively
- Include section even if it has no courses (empty courses array)
- All subject names should be the full descriptive English course title
- Do NOT include any credit hours, grades, or numerical data
"""
