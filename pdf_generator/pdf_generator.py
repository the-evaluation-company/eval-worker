"""
PDF Generator Main Class

This module contains the main PDF generator class that orchestrates
the entire PDF generation process.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import BLACK_COLOR, PDF_CONFIG
from .core import PDFDocument
from .types import CaseInfo, CredentialGroup, PDFGenerationOptions
from .utils import normalize_text, wrap_text


class PDFGenerator:
    """Main PDF generator class for creating evaluation reports"""

    def __init__(self):
        self.document = PDFDocument()
        self.config = PDF_CONFIG
        self.current_page_number = 1
        self.total_pages = 1

    def generate_pdf(self, credential_groups: List[CredentialGroup], case_info: CaseInfo, options: PDFGenerationOptions = None) -> bytes:
        """
        Generate PDF evaluation report.

        Args:
            credential_groups: List of credential groups to include
            case_info: Case information for the report
            options: PDF generation options

        Returns:
            PDF document as bytes
        """
        if options is None:
            options = PDFGenerationOptions()

        # Create first page without footer
        self.document.add_page_with_background()

        # Start with top margin
        current_y = self.document.page_height - self.config.layout.TOP_MARGIN

        # Draw credential information
        current_y = self._draw_credential_info(current_y, credential_groups[0] if credential_groups else None, case_info)

        # Add spacing before credentials
        current_y -= self.config.layout.LINE_HEIGHT * self.config.spacing.SECTION_BREAK

        # Draw equivalency box
        if credential_groups:
            current_y = self._draw_equivalency_box(current_y, credential_groups[0], options)

        # Draw credential details for each group
        for i, group in enumerate(credential_groups):
            # Check if we need a new page for credential details
            estimated_lines_needed = 7
            estimated_space_needed = estimated_lines_needed * self.config.layout.LINE_HEIGHT

            if current_y - estimated_space_needed < 100:
                # Create new page
                self.current_page_number += 1
                self.total_pages = max(self.total_pages, self.current_page_number)

                # Add new page with background
                self.document.add_page_with_background()
                current_y = self.document.page_height - self.config.layout.TOP_MARGIN

            # Draw credential details
            current_y = self._draw_credential_details(current_y, group, i + 1, len(credential_groups))

            # Add spacing between credentials
            if i < len(credential_groups) - 1:
                current_y -= self.config.spacing.SECTION_BREAK * self.config.layout.LINE_HEIGHT

        # Check if we need a new page for comments section
        if len(credential_groups) > 2 or current_y < 200:
            # Create new page for comments
            self.current_page_number += 1
            self.total_pages = max(self.total_pages, self.current_page_number)

            # Add new page with background
            self.document.add_page_with_background()
            current_y = self.document.page_height - self.config.layout.TOP_MARGIN
        else:
            # Add spacing before comments
            current_y -= self.config.layout.LINE_HEIGHT * self.config.spacing.SECTION_BREAK

        # Draw comments section
        current_y = self._draw_comments_section(current_y)

        # Add policy page at the end of the document
        self.current_page_number += 1
        self.total_pages = max(self.total_pages, self.current_page_number)

        # Add new page for policies
        self.document.add_page_with_background()
        current_y = self.document.page_height - self.config.layout.TOP_MARGIN

        # Draw policy statements
        current_y = self._draw_policy_statements(current_y)

        # Draw page numbering
        self._draw_page_numbering(case_info)

        # Save and return document
        return self.document.save_document()

    def generate_evaluation_report_enhanced_style(
        self, evaluation_type: str, credential_groups: List[Dict[str, Any]], evaluation_data: Dict[str, Any], student_name: str, case_info: Dict[str, str]
    ) -> bytes:
        """
        Generate PDF evaluation report.

        Args:
            evaluation_type: Type of evaluation (general, cbc, etc.)
            credential_groups: List of credential groups as dictionaries
            evaluation_data: Evaluation data dictionary
            student_name: Student name
            case_info: Case information dictionary

        Returns:
            PDF document as bytes
        """
        # Convert dictionary data to internal types
        converted_credential_groups = []
        for group_dict in credential_groups:
            credential_group = CredentialGroup(
                id=group_dict.get("id", ""),
                country=group_dict.get("country", ""),
                institution=group_dict.get("institution", ""),
                program=group_dict.get("program", ""),
                usEquivalency=group_dict.get("usEquivalency", ""),
                programLength=group_dict.get("programLength", ""),
                awardDate=group_dict.get("awardDate", ""),
                dateOfAttendance=group_dict.get("dateOfAttendance", ""),
                programOfStudy=group_dict.get("programOfStudy", ""),
                programOfStudyEnglishName=group_dict.get("programOfStudyEnglishName", ""),
                institutionEnglishName=group_dict.get("institutionEnglishName", ""),
                englishCredential=group_dict.get("englishCredential", ""),
                notes=group_dict.get("notes", ""),
                courseworkCompletedDate=group_dict.get("courseworkCompletedDate", ""),
                documents=group_dict.get("documents", []),
            )
            converted_credential_groups.append(credential_group)

        # Convert case info
        converted_case_info = CaseInfo(
            caseNumber=case_info.get("caseNumber", ""),
            nameOnApplication=case_info.get("nameOnApplication", ""),
            dateOfBirth=case_info.get("dateOfBirth", ""),
            verificationStatus=case_info.get("verificationStatus", ""),
        )

        # Create options based on evaluation type
        options = PDFGenerationOptions(title="Credential Evaluation", includeHeader=True, includeFooter=True, analysis_type=evaluation_type)

        # Generate PDF
        return self._generate_enhanced_style_pdf(converted_credential_groups, converted_case_info, options, evaluation_type, evaluation_data, student_name)

    def _generate_enhanced_style_pdf(
        self,
        credential_groups: List[CredentialGroup],
        case_info: CaseInfo,
        options: PDFGenerationOptions,
        evaluation_type: str,
        evaluation_data: Dict[str, Any],
        student_name: str,
    ) -> bytes:
        """
        Generate PDF.

        """
        # Create first page without footer
        self.document.add_page_with_background()

        # Start with top margin
        current_y = self.document.page_height - 120  # Top margin

        # Draw header section
        current_y = self._draw_enhanced_header(current_y, case_info, student_name, evaluation_type)

        # Draw equivalency box
        if credential_groups:
            current_y = self._draw_enhanced_equivalency_box(current_y, credential_groups[0], evaluation_type)

        # Draw credential details
        for i, group in enumerate(credential_groups):
            # Check if we need a new page for credential details
            estimated_lines_needed = 7
            estimated_space_needed = estimated_lines_needed * self.config.layout.LINE_HEIGHT

            if current_y - estimated_space_needed < 100:
                # Create new page
                self.current_page_number += 1
                self.total_pages = max(self.total_pages, self.current_page_number)

                # Add new page with background and footer
                self.document.add_page_with_background()
                current_y = self.document.page_height - self.config.layout.TOP_MARGIN

            # Draw credential details
            current_y = self._draw_enhanced_credential_details(current_y, group, i + 1, len(credential_groups))

            # Add spacing between credentials
            if i < len(credential_groups) - 1:
                current_y -= 40  # Spacing between credentials

        # Check if we need a new page for comments section
        if len(credential_groups) > 2 or current_y < 200:
            # Create new page for comments
            self.current_page_number += 1
            self.total_pages = max(self.total_pages, self.current_page_number)

            # Add new page with background and footer (no footer for comments page)
            self.document.add_page_with_background()
            current_y = self.document.page_height - self.config.layout.TOP_MARGIN
        else:
            # Add spacing before comments
            current_y -= self.config.layout.LINE_HEIGHT * self.config.spacing.SECTION_BREAK

        # Draw footer section
        current_y = self._draw_enhanced_footer(current_y)

        # Add policy page at the end of the document
        self.current_page_number += 1
        self.total_pages = max(self.total_pages, self.current_page_number)

        # Add new page for policies
        self.document.add_page_with_background()
        current_y = self.document.page_height - self.config.layout.TOP_MARGIN

        # Draw policy statements
        current_y = self._draw_policy_statements(current_y)

        # Draw page numbering - add to all pages
        self._draw_enhanced_page_numbering(case_info, student_name)

        # Save and return document
        return self.document.save_document()

    def _draw_enhanced_header(self, current_y: float, case_info: CaseInfo, student_name: str, evaluation_type: str) -> float:
        """
        Draw header section in enhanced style.
        """
        # Get current date
        date_string = datetime.now().strftime("%B %d, %Y")

        # Header layout with correct evaluation type
        evaluation_type_text = self._get_evaluation_type_text(evaluation_type)

        header_info = [
            {"label": "Date:", "value": date_string},
            {"label": "SpanTran Number:", "value": case_info.caseNumber},
            {"label": "Name on Application:", "value": case_info.nameOnApplication or student_name},
            {"label": "Name on Documentation:", "value": case_info.nameOnApplication or student_name},
            {"label": "Date of Birth:", "value": case_info.dateOfBirth or "Not Available"},
            {"label": "Type of Evaluation:", "value": evaluation_type_text},
        ]

        # Calculate label width for alignment
        max_label_width = max(self.document.get_text_width(item["label"], 9, "bold") for item in header_info)

        # Positioning
        label_x = 35
        value_x = label_x + max_label_width + 20

        # Draw each info item
        for info in header_info:
            # Draw label
            self.document.draw_text(normalize_text(info["label"]), label_x, current_y, 9, "bold", BLACK_COLOR)

            # Determine if value should be bold
            should_be_bold = info["label"] in ["SpanTran Number:", "Name on Application:", "Name on Documentation:"]

            # Draw value
            self.document.draw_text(
                normalize_text(info["value"]),
                value_x,
                current_y,
                9,
                "bold" if should_be_bold else "regular",
                BLACK_COLOR,
            )

            current_y -= 12  # TypeScript line height

        return current_y

    def _get_evaluation_type_text(self, evaluation_type: str) -> str:
        """
        Get the correct evaluation type text.
        """
        evaluation_type_mapping = {
            "general": "General Analysis",
            "cbc": "Course-by-Course Analysis",
            "document": "Document Analysis",
            "hybrid": "Hybrid Analysis",
            "comprehensive": "Comprehensive Analysis",
        }
        return evaluation_type_mapping.get(evaluation_type, "General Analysis")

    def _draw_enhanced_equivalency_box(self, current_y: float, form_data: CredentialGroup, evaluation_type: str) -> float:
        """
        Draw equivalency box in enhanced style.
        """
        # Add empty line between Type of Evaluation and CREDENTIALS SUMMARY
        current_y -= 12

        # Draw CREDENTIALS SUMMARY header
        self.document.draw_text(
            "CREDENTIALS SUMMARY",
            35,  # TypeScript left margin
            current_y,
            9,
            "bold",
            BLACK_COLOR,
        )

        current_y -= 20

        # Get equivalency text
        program_value = form_data.program or form_data.programOfStudyEnglishName or ""
        equivalency_value = form_data.usEquivalency or program_value or ""
        equivalency_text = normalize_text(f"Recommended U.S. Equivalency: {equivalency_value}")

        # Box dimensions
        available_width = self.document.get_available_width()
        line_spacing = 12 * 1.2
        box_width = available_width  # TypeScript padding

        # Calculate text width inside the box (accounting for internal margins)
        box_left_margin = 50 - 35  # Text position (50) minus box position (35)
        box_right_margin = box_left_margin  # Same margin on both sides
        text_available_width = available_width - box_left_margin - box_right_margin

        # Wrap text
        wrapped_lines = wrap_text(equivalency_text, self.document.font_manager, 12, text_available_width, "bold")

        # Calculate box height
        box_height = len(wrapped_lines) * line_spacing + 16

        # Draw box
        self.document.draw_rectangle(
            35, current_y - box_height + line_spacing - 15, box_width, box_height, BLACK_COLOR, 1  # TypeScript left margin  # TypeScript positioning
        )

        # Draw text in box
        line_y = current_y - 15
        for line in wrapped_lines:
            self.document.draw_text(
                normalize_text(line),
                50,  # TypeScript text margin
                line_y,
                12,
                "bold",
                BLACK_COLOR,
            )
            line_y -= line_spacing

        current_y = current_y - box_height + line_spacing

        # Add spacing after box
        current_y -= 50

        return current_y

    def _draw_enhanced_credential_details(self, current_y: float, form_data: CredentialGroup, credential_index: int, total_credentials: int) -> float:
        """
        Draw credential details in enhanced style.
        """
        # Add spacing
        current_y -= 12

        # Draw credential header
        self.document.draw_text(
            f"CREDENTIAL {credential_index} of {total_credentials}",
            50,  # Match new left margin
            current_y,
            9,
            "bold",
            BLACK_COLOR,
        )

        current_y -= 20

        # Prepare credential details
        program_value = form_data.program or form_data.programOfStudyEnglishName or ""

        credential_details = [
            {"label": "Country of Study:", "value": form_data.country or ""},
            {"label": "Institution:", "value": form_data.institution or ""},
            {"label": "Foreign Credential:", "value": program_value},
            {"label": "Length of Program:", "value": form_data.programLength or ""},
            {"label": "Recommended U.S. Equivalency:", "value": form_data.usEquivalency or ""},
        ]

        # Add optional fields
        if form_data.notes:
            credential_details.append({"label": "Notes:", "value": form_data.notes})

        # Calculate label width for alignment
        max_label_width = max(self.document.get_text_width(detail["label"], 9, "bold") for detail in credential_details)

        # Positioning - move everything right and increase spacing between label and value
        label_x = 50  # Move right from 35 to 50
        value_x = label_x + max_label_width + 25  # Increased spacing from 15 to 25

        # Draw each detail
        for detail in credential_details:
            if not detail["value"]:
                continue

            # Determine font style for label
            # "Recommended U.S. Equivalency:" should be bold italic
            is_equivalency_label = detail["label"] == "Recommended U.S. Equivalency:"

            # Draw label
            self.document.draw_text(normalize_text(detail["label"]), label_x, current_y, 9, "bold", BLACK_COLOR)

            # Calculate available width for value - match left margin (50px) on right side
            right_margin = 50  # Match the left margin
            available_width = self.document.page_width - value_x - right_margin

            # Wrap text for long values (especially Recommended U.S. Equivalency)
            if len(detail["value"]) > 80 or is_equivalency_label:  # Increased threshold for better wrapping
                # Special handling for Recommended U.S. Equivalency to ensure proper wrapping
                is_notes_label = detail["label"] == "Notes:"
                if is_equivalency_label:
                    # Split at "regionally-accredited institution" for better formatting
                    split_phrase = "regionally-accredited institution"
                    if split_phrase in detail["value"]:
                        parts = detail["value"].split(split_phrase)
                        if len(parts) == 2:
                            first_part = parts[0] + split_phrase
                            second_part = parts[1]
                            wrapped_lines = [first_part, second_part]
                        else:
                            wrapped_lines = wrap_text(detail["value"], self.document.font_manager, 9, available_width, "bold")
                    else:
                        wrapped_lines = wrap_text(detail["value"], self.document.font_manager, 9, available_width, "bold")
                elif is_notes_label:
                    # Notes should not be bold but should wrap
                    wrapped_lines = wrap_text(detail["value"], self.document.font_manager, 9, available_width, "regular")
                else:
                    wrapped_lines = wrap_text(detail["value"], self.document.font_manager, 9, available_width, "regular")

                # Draw first line with appropriate font weight
                if is_equivalency_label:
                    value_font_type = "bold"  # Equivalency statement should be bold
                elif is_notes_label:
                    value_font_type = "regular"  # Notes should be regular
                else:
                    value_font_type = "regular"
                    
                self.document.draw_text(normalize_text(wrapped_lines[0]), value_x, current_y, 9, value_font_type, BLACK_COLOR)

                # Draw additional lines if any
                for line in wrapped_lines[1:]:
                    current_y -= 12  # Move to next line
                    self.document.draw_text(normalize_text(line), value_x, current_y, 9, value_font_type, BLACK_COLOR)

                current_y -= 12  # Extra spacing after wrapped text
            else:
                # Draw single line value with appropriate font weight
                if is_equivalency_label:
                    value_font_type = "bold"  # Equivalency statement should be bold
                elif detail["label"] == "Notes:":
                    value_font_type = "regular"  # Notes should be regular
                else:
                    value_font_type = "regular"
                self.document.draw_text(normalize_text(detail["value"]), value_x, current_y, 9, value_font_type, BLACK_COLOR)

            current_y -= 12  # TypeScript line height

        return current_y

    def _draw_enhanced_footer(self, current_y: float) -> float:
        """
        Draw footer section in enhanced style.
        """
        # Draw comments header
        self.document.draw_text("Comments:", 35, current_y, 9, "bold", BLACK_COLOR)  # TypeScript left margin

        current_y -= 18

        # Draw comments text
        comments_text = """The Evaluation Company is a member of the National Association of Credential Evaluation Services (NACES). This evaluation is advisory only.

All documentation submitted to TEC is reviewed internally. At a minimum, TEC requires authentication of the highest post-secondary academic credential per country of study as well as professional credentials from most countries. TEC also requires authentication of secondary school credentials from Vietnam, Dominican Republic, Haiti, and all member countries of the West African Examinations Council. As of the original issuance of this evaluation, verification of authenticity is not possible for most credentials from Afghanistan, Cuba, Eritrea, Gaza Strip, Libya, Myanmar, Sudan, Syria, Turkmenistan, Ukraine, and Yemen. Any exceptions will be noted in the body of this report."""

        # Split into paragraphs and wrap each separately
        paragraphs = comments_text.split("\n\n")
        wrapped_lines = []

        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                # Wrap current paragraph
                paragraph_lines = wrap_text(
                    paragraph.strip(),
                    self.document.font_manager,
                    10,
                    self.document.get_available_width(),
                    "regular",
                )
                wrapped_lines.extend(paragraph_lines)
                print(f"DEBUG: Wrapped lines: {paragraph_lines}")

                # Add empty line between paragraphs (except after last paragraph)
                if i < len(paragraphs) - 1:
                    wrapped_lines.append("")

        for line in wrapped_lines:
            if line:  # Draw text only if line is not empty
                self.document.draw_text(line, 35, current_y, 10, "regular", BLACK_COLOR)  # TypeScript left margin
            # Move to next line regardless (empty lines create spacing)
            current_y -= 11  # TypeScript line height

        # Add retention date
        retention_date = datetime.now()
        retention_date = retention_date.replace(year=retention_date.year + 5)
        formatted_retention_date = retention_date.strftime("%B %d, %Y")

        # Add empty line before retention text
        current_y -= 24

        retention_text = f"Records pertaining to this file will be retained until {formatted_retention_date}"

        self.document.draw_text(retention_text, 35, current_y, 10, "bold", BLACK_COLOR)  # TypeScript left margin

        current_y -= 18

        # Add prepared by line
        self.document.draw_text("Prepared by: The Evaluation Company", 35, current_y, 10, "regular", BLACK_COLOR)  # TypeScript left margin

        current_y -= 11  # Move to next line

        # Add issuing office
        self.document.draw_text("Issuing Office - Houston, TX", 35, current_y, 10, "bold", BLACK_COLOR)  # TypeScript left margin

        return current_y

    def _draw_policy_statements(self, current_y: float) -> float:
        """
        Draw policy statements section in enhanced style.
        """
        # Policy statements text
        policy_text = """General Information and Policy Statements for Services

Located in Houston, Texas, New York, New York, Miami, Florida (intake office), and Los Angeles, California (intake office). The Evaluation Company referred to herein as TEC, provides academic credential evaluations, verification, and translations. TEC was incorporated in Texas in 1989, and joined the National Association of Credential Evaluation Services (NACES®) as a regular member in 1996.

TEC does not discriminate on the basis of race, disability, religion, gender, national origin, or age. However, as a private company not supported by any governmental or public funds, TEC retains the right to decline to provide services according to internal business practices and policies.

TEC retains evaluations and translations for five years from the date of file initiation. Questions regarding completed services must be submitted in writing within 30 calendar days of the date the evaluation was issued. Questions submitted after 30 calendar days must be submitted in writing, and accompanied by a non-refundable revision fee of $50.00. This fee covers administrative costs and does not guarantee that any modifications will be made to the evaluation.

Credential Evaluation Policies

The U.S. government does not set standards for the evaluation of foreign educational credentials. TEC bases its evaluations on extensive in-house research, information gained through participation in professional development opportunities, and on-line and print resources. TEC is a member of NACES® but evaluation methodologies and outcomes vary among NACES member organizations. The recipient retains the right to accept, modify, or reject the recommendation(s) listed on the evaluation.

TEC does not knowingly evaluate falsified or altered documents. In cases of confirmed forgeries, TEC shares this information with NACES member organizations and notifies other entities as deemed appropriate.

General Analysis evaluations state recommended U.S. equivalency/ies and establish recognition/accreditation. Course Analysis evaluations additionally list coursework with a converted U.S. grade and credit value for each course, and a cumulative grade point average. Divisional Course Analysis evaluations provide the same information and also indicate the course level as follows: L = lower level (required prerequisites and entry-level undergraduate coursework), U = upper level (advanced-level undergraduate coursework), and G = graduate level (beyond undergraduate level coursework). Engineering and Teacher Course Analysis evaluations group courses by category. Nursing Course Analysis evaluations provide the same information as Divisional Course Analysis evaluations, and also include clinical and/or practical training if listed on the submitted documentation.

Course Analysis evaluations include recommended U.S. semester credit hours. In the U.S., one semester credit hour requires a minimum of 15 contact hours of theoretical instruction or 30 to 45 contact hours of laboratory and/or practical instruction per semester. A typical student enrolled in full-time studies in U.S. higher education earns approximately 30 semester credit hours per academic year.

TEC converts foreign academic credits, units, hours, etc. into U.S. semester credit hours regardless of the number of foreign credits, units, hours earned or completed. Courses may be assigned a lower number of U.S. semester credit hours than the applicant expects to receive; some courses may receive only one or two credits while others may receive no credit at all. Evaluations state the total recommended credit hours and may list courses for which no U.S. credit is recommended.

Foreign grades are converted to U.S. letter grades based on the 4.00 system. Letter grade values are generally: A = 4.00, A- = 3.67, B+ = 3.33, B = 3.00, B- = 2.67, C+ = 2.33, C = 2.00, C- = 1.67, D+ = 1.33, D = 1.00, D- = 0.67/D-, F = 0.00. A grade point average/GPA is a weighted average by which recommended credits per course are multiplied by the 4.00-based grade per course arriving at quality points. The total number of quality points are then divided by the total number of attempted credits. TEC lists the equivalent grade per course, including failures, incomplete, withdrawn, and pass grades. Failures are included in grade point average calculation. In cases of pass/fail grades, pass grades are awarded credit but not factored into the grade point average. If a specific course is attempted multiple times, the evaluation only includes the first and final attempts. The cumulative grade point average/CGPA will reflect both grades."""

        # Split text into paragraphs
        paragraphs = policy_text.split("\n\n")

        for paragraph in paragraphs:
            if paragraph.strip():
                # Check if this is a header
                is_header = paragraph.strip() in ["General Information and Policy Statements for Services", "Credential Evaluation Policies"]

                # Use appropriate font size and type
                font_size = 9 if is_header else 8
                font_type = "times-bold" if is_header else "times"

                # Wrap text
                wrapped_lines = wrap_text(paragraph.strip(), self.document.font_manager, font_size, self.document.get_available_width(), font_type)

                # Draw each line
                for line in wrapped_lines:
                    # Check if we need a new page
                    if current_y < 50:
                        # Create new page
                        self.current_page_number += 1
                        self.total_pages = max(self.total_pages, self.current_page_number)

                        # Add new page with background and footer (no footer for policy pages)
                        self.document.add_page_with_background()
                        current_y = self.document.page_height - self.config.layout.TOP_MARGIN - 20  # Maintain extra margin on new pages

                    # Draw the line
                    self.document.draw_text(line, self.config.layout.LEFT_MARGIN, current_y, font_size, font_type, BLACK_COLOR)  # Use config margin
                    current_y -= font_size + 2  # Line height

                # Add spacing between paragraphs
                current_y -= 10

        return current_y

    def _draw_enhanced_page_numbering(self, case_info: CaseInfo, student_name: str = None):
        """
        Draw page numbering in enhanced style with case info.
        """
        # Format student name for display
        if student_name:
            # Split name and take last name, first name
            name_parts = student_name.split()
            if len(name_parts) >= 2:
                last_name = name_parts[-1]
                first_name = name_parts[0]
                display_name = f"{last_name}, {first_name}"
            else:
                display_name = student_name
        else:
            display_name = "Unknown"

        # Create complete page numbering text as one string
        full_text = f"TEC NO.: {case_info.caseNumber} * {display_name} * Page {self.current_page_number} of {self.total_pages}"

        # Calculate total width for centering
        total_width = self.document.get_text_width(full_text, 9, "bold")

        # Position at bottom center of page
        x_position = (self.document.page_width - total_width) / 2
        y_position = 30  # Bottom margin

        # Draw complete text as one unit (bold)
        self.document.draw_text(full_text, x_position, y_position, 9, "bold", BLACK_COLOR)

    def _draw_page_numbering(self, case_info: CaseInfo, student_name: str = None):
        """
        Draw page numbering in standard style with case info.
        """
        # Format student name for display
        if student_name:
            # Split name and take last name, first name
            name_parts = student_name.split()
            if len(name_parts) >= 2:
                last_name = name_parts[-1]
                first_name = name_parts[0]
                display_name = f"{last_name}, {first_name}"
            else:
                display_name = student_name
        else:
            display_name = "Unknown"

        # Create complete page numbering text as one string
        full_text = f"TEC NO.: {case_info.caseNumber} * {display_name} * Page {self.current_page_number} of {self.total_pages}"

        # Calculate total width for centering
        total_width = self.document.get_text_width(full_text, 9, "bold")

        # Position at bottom center of page
        x_position = (self.document.page_width - total_width) / 2
        y_position = 30  # Bottom margin

        # Draw complete text as one unit (bold)
        self.document.draw_text(full_text, x_position, y_position, 9, "bold", BLACK_COLOR)

    def _draw_credential_info(self, current_y: float, form_data: Optional[CredentialGroup], case_info: CaseInfo) -> float:
        """
        Draw credential information section.

        Args:
            current_y: Current Y position
            form_data: Form data for the credential
            case_info: Case information

        Returns:
            New Y position
        """
        # Get current date
        date_string = datetime.now().strftime("%B %d, %Y")

        # Prepare credential info items
        name_on_application = case_info.nameOnApplication or "NAME_MISSING"
        name_on_documentation = case_info.nameOnApplication or "NAME_MISSING"
        dob = case_info.dateOfBirth or "Not Available"

        credential_info = [
            {"label": "Date:", "value": date_string},
            {"label": "SpanTran Number:", "value": case_info.caseNumber},
            {"label": "Name on Application:", "value": name_on_application},
            {"label": "Name on Documentation:", "value": name_on_documentation},
            {"label": "Date of Birth:", "value": dob},
            {"label": "Type of Evaluation:", "value": "General Analysis"},
        ]

        # Calculate label width for alignment
        max_label_width = max(self.document.get_text_width(item["label"], self.config.fonts.NORMAL_SIZE, "bold") for item in credential_info)

        # Calculate positions for student info section
        student_value_x_position = self.config.layout.STUDENT_INFO_MARGIN + max_label_width + 50

        # Draw each info item
        for info in credential_info:
            # Draw label with original margin (keep labels in place)
            self.document.draw_text(
                normalize_text(info["label"]), self.config.layout.LEFT_MARGIN, current_y, self.config.fonts.NORMAL_SIZE, "bold", BLACK_COLOR
            )

            # Determine if value should be bold
            should_be_bold = info["label"] in ["SpanTran Number:", "Name on Application:", "Name on Documentation:"]

            # Draw value with shifted position (only values are shifted left)
            self.document.draw_text(
                normalize_text(info["value"]),
                student_value_x_position,
                current_y,
                self.config.fonts.NORMAL_SIZE,
                "bold" if should_be_bold else "regular",
                BLACK_COLOR,
            )

            current_y -= self.config.layout.LINE_HEIGHT

        return current_y

    def _draw_equivalency_box(self, current_y: float, form_data: CredentialGroup, options: PDFGenerationOptions) -> float:
        """
        Draw equivalency box section.

        Args:
            current_y: Current Y position
            form_data: Form data for the credential
            options: PDF generation options

        Returns:
            New Y position
        """
        # Get equivalency text with proper label
        # Use programOfStudyEnglishName as fallback for program
        program_value = form_data.program or form_data.programOfStudyEnglishName or ""
        equivalency_value = form_data.usEquivalency or program_value or ""
        equivalency_text = normalize_text(f"Recommended U.S. Equivalency: {equivalency_value}")

        # Calculate box dimensions
        available_width = self.document.get_available_width()
        line_spacing = self.config.fonts.EQUIVALENCY_SIZE * 1.2
        box_width = available_width + self.config.layout.HORIZONTAL_PADDING * 2

        # Calculate text width inside the box (accounting for internal margins)
        # Text position: LEFT_MARGIN + HORIZONTAL_PADDING - 10
        # Box position: LEFT_MARGIN
        box_internal_margin = self.config.layout.HORIZONTAL_PADDING - 10
        text_available_width = available_width - (box_internal_margin * 2)

        # Wrap text
        wrapped_lines = wrap_text(
            equivalency_text,
            self.document.font_manager,
            self.config.fonts.EQUIVALENCY_SIZE,
            text_available_width,
            "bold",
        )

        # Calculate box height
        box_height = len(wrapped_lines) * line_spacing + self.config.layout.VERTICAL_PADDING * 1.1

        # Draw box with additional spacing to avoid overlap with header
        self.document.draw_rectangle(
            self.config.layout.LEFT_MARGIN, current_y - box_height + line_spacing - 20, box_width, box_height, BLACK_COLOR, 1  # Added 20 points spacing
        )

        # Draw text in box with adjusted position to match the shifted frame
        line_y = current_y - 20  # Shift text down by 20 points to match frame
        for line in wrapped_lines:
            self.document.draw_text(
                normalize_text(line),
                self.config.layout.LEFT_MARGIN + self.config.layout.HORIZONTAL_PADDING - 10,
                line_y,
                self.config.fonts.EQUIVALENCY_SIZE,
                "bold",
                BLACK_COLOR,
            )
            line_y -= line_spacing

        current_y = current_y - box_height + line_spacing

        # Add spacing after box
        current_y -= 24

        return current_y

    def _draw_credential_details(self, current_y: float, form_data: CredentialGroup, credential_index: int, total_credentials: int) -> float:
        """
        Draw credential details section.

        Args:
            current_y: Current Y position
            form_data: Form data for the credential
            credential_index: Index of current credential
            total_credentials: Total number of credentials

        Returns:
            New Y position
        """
        # Add spacing
        current_y -= self.config.layout.LINE_HEIGHT * 1.0

        # Draw credential header
        self.document.draw_text(
            f"CREDENTIAL {credential_index} of {total_credentials}",
            self.config.layout.LEFT_MARGIN,
            current_y,
            self.config.fonts.NORMAL_SIZE,
            "bold",
            BLACK_COLOR,
        )

        current_y -= self.config.layout.LINE_HEIGHT * 1.8

        # Prepare credential details
        # Use programOfStudyEnglishName as fallback for program
        program_value = form_data.program or form_data.programOfStudyEnglishName or ""

        credential_details = [
            {"label": "Country of Study:", "value": form_data.country or ""},
            {"label": "Institution:", "value": form_data.institution or ""},
            {"label": "Foreign Credential:", "value": program_value},
            {"label": "Length of Program:", "value": form_data.programLength or ""},
            {"label": "Recommended U.S. Equivalency:", "value": form_data.usEquivalency or ""},
        ]

        # Add optional fields
        if form_data.notes:
            credential_details.append({"label": "Notes:", "value": form_data.notes})

        # Calculate label width for alignment
        max_label_width = max(self.document.get_text_width(detail["label"], self.config.fonts.NORMAL_SIZE, "bold") for detail in credential_details)

        # Calculate position for credential details values (same as student info)
        credential_value_x_position = self.config.layout.STUDENT_INFO_MARGIN + max_label_width + 10

        # Draw each detail
        for detail in credential_details:
            if not detail["value"]:
                continue

            # Draw label (keep original position)
            self.document.draw_text(
                normalize_text(detail["label"]), self.config.layout.LEFT_MARGIN, current_y, self.config.fonts.NORMAL_SIZE, "bold", BLACK_COLOR
            )

            # Draw value (shifted to match student info values)
            self.document.draw_text(
                normalize_text(detail["value"]), credential_value_x_position, current_y, self.config.fonts.NORMAL_SIZE, "regular", BLACK_COLOR
            )

            current_y -= self.config.layout.LINE_HEIGHT

        return current_y

    def _draw_comments_section(self, current_y: float) -> float:
        """
        Draw comments section.

        Args:
            current_y: Current Y position

        Returns:
            New Y position
        """
        # Draw comments header
        self.document.draw_text("Comments:", self.config.layout.LEFT_MARGIN, current_y, self.config.fonts.NORMAL_SIZE, "bold", BLACK_COLOR)

        current_y -= self.config.layout.LINE_HEIGHT * 1.5

        # Draw comments text
        comments_text = """The Evaluation Company is a member of the National Association of Credential Evaluation Services (NACES). This evaluation is advisory only.

All documentation submitted to TEC is reviewed internally. At a minimum, TEC requires authentication of the highest post-secondary academic credential per country of study as well as professional credentials from most countries. TEC also requires authentication of secondary school credentials from Vietnam, Dominican Republic, Haiti, and all member countries of the West African Examinations Council. As of the original issuance of this evaluation, verification of authenticity is not possible for most credentials from Afghanistan, Cuba, Eritrea, Gaza Strip, Libya, Myanmar, Sudan, Syria, Turkmenistan, Ukraine, and Yemen. Any exceptions will be noted in the body of this report."""

        # Split into paragraphs and wrap each separately
        paragraphs = comments_text.split("\n\n")
        wrapped_lines = []

        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                # Wrap current paragraph
                paragraph_lines = wrap_text(
                    paragraph.strip(),
                    self.document.font_manager,
                    self.config.fonts.COMMENTS_SIZE,
                    self.document.get_available_width(),
                    "regular",
                )
                wrapped_lines.extend(paragraph_lines)

                # Add empty line between paragraphs (except after last paragraph)
                if i < len(paragraphs) - 1:
                    wrapped_lines.append("")

        for line in wrapped_lines:
            if line:  # Draw text only if line is not empty
                self.document.draw_text(line, self.config.layout.LEFT_MARGIN, current_y, self.config.fonts.COMMENTS_SIZE, "regular", BLACK_COLOR)
            # Move to next line regardless (empty lines create spacing)
            current_y -= self.config.layout.LINE_HEIGHT * 0.9

        # Add retention date
        retention_date = datetime.now()
        retention_date = retention_date.replace(year=retention_date.year + 5)
        formatted_retention_date = retention_date.strftime("%B %d, %Y")

        # Add empty line before retention text
        current_y -= self.config.layout.LINE_HEIGHT * 2

        retention_text = f"Records pertaining to this file will be retained until {formatted_retention_date}"

        self.document.draw_text(retention_text, self.config.layout.LEFT_MARGIN, current_y, self.config.fonts.COMMENTS_SIZE, "bold", BLACK_COLOR)

        current_y -= self.config.layout.LINE_HEIGHT * self.config.spacing.PARAGRAPH_BREAK

        # Add prepared by line
        self.document.draw_text(
            "Prepared by: The Evaluation Company", self.config.layout.LEFT_MARGIN, current_y, self.config.fonts.COMMENTS_SIZE, "regular", BLACK_COLOR
        )

        current_y -= self.config.layout.LINE_HEIGHT

        # Add issuing office
        self.document.draw_text("Issuing Office - Houston, TX", self.config.layout.LEFT_MARGIN, current_y, self.config.fonts.COMMENTS_SIZE, "bold", BLACK_COLOR)

        return current_y
