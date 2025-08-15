"""
Course Extraction Instructions

Modular prompt for extracting course information from academic transcripts.
This prompt is injected into CBC analysis instructions.
"""

COURSE_EXTRACTION_INSTRUCTIONS = """
**COURSE EXTRACTION SECTION:**

Extract course names from the English translations of the documents found in the pdf (you do not need translate yourself, translations are given). Focus on:

1. **Section Headers**: Academic periods (e.g., "ACADEMIC YEAR 1992 SEMESTER 1", "EXAMINATION 1992", "Fall 2020", "Term I")
2. **Course Names**: Extract only the English course/subject names from the English translation

**Course Extraction Rules:**
- ONLY extract course names from English translation sections (English translations are always present)
- Extract subjects in Title Case
- Preserve exact section header text as it appears
- Use ONLY the English course names - ignore original foreign language course names
- Maintain document order exactly - do not reorder sections or courses
- Include courses even if they appear without grades or credits
- Extract foreign credits and foreign grades as shown in the document
- For grades that are variations of "pass" (e.g., "P", "PASS", "S", "Satisfactory"), use "PASS" as the grade
- Focus on the descriptive course titles/names
- **Section Naming**: Use "ACADEMIC YEAR [year] SEMESTER [number]" format for regular academic periods. Use "EXAMINATION [year/date info]" format when grades are from examinations

**Course JSON Structure:**
For each credential, add a "course_analysis" section containing course names, credits, and grades:

```json
"course_analysis": {
  "sections": [
    {
      "section_name": "ACADEMIC YEAR 1992 SEMESTER 1",
      "courses": [
        {
          "subject": "Communication and Language",
          "foreign_credits": "3",
          "foreign_grades": "A"
        },
        {
          "subject": "Study and Understanding of Man",
          "foreign_credits": "2",
          "foreign_grades": "PASS"
        }
      ]
    },
    {
      "section_name": "EXAMINATION 1992", 
      "courses": [
        {
          "subject": "General Pedagogy",
          "foreign_credits": "4",
          "foreign_grades": "B+"
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
- Include foreign credits and foreign grades as they appear in the document
- For any grade variations of "pass" (P, PASS, S, Satisfactory, etc.), standardize to "PASS"
"""
