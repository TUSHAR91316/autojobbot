import re
from pathlib import Path
from typing import Dict, Any, Optional
from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract plain text from PDF using pypdf"""
    text_chunks = []
    try:
        reader = PdfReader(str(file_path))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    return "\n".join(text_chunks).strip()


def extract_text_from_docx(file_path: Path) -> str:
    """Extract plain text from DOCX using python-docx"""
    text_chunks = []
    try:
        doc = Document(str(file_path))
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text_chunks.append(paragraph.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text:
                        text_chunks.append(cell.text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    return "\n".join(text_chunks).strip()


def extract_text_from_txt(file_path: Path) -> str:
    """Extract plain text from TXT or Markdown file"""
    try:
        return file_path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1", errors="ignore").strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from file: {str(e)}")


def clean_latex_code(latex_code: str) -> str:
    """
    Parse LaTeX resume source code into clean, structured plain text.
    Strips preamble, commands, macro wrappers, comments, and unescapes LaTeX entities.
    """
    # 1. Remove comments: lines or segments starting with unescaped %
    lines = []
    for line in latex_code.splitlines():
        clean_line = re.sub(r"(?<!\\)%.*$", "", line).strip()
        lines.append(clean_line)
    text = "\n".join(lines)

    # 2. Strip preamble before \begin{document} if present
    if r"\begin{document}" in text:
        text = text.split(r"\begin{document}", 1)[1]
    if r"\end{document}" in text:
        text = text.split(r"\end{document}", 1)[0]

    # 3. Section and subsection headings
    text = re.sub(r"\\(sub)?section\*?\{([^}]+)\}", r"\n\n\2\n", text)

    # 4. Links and URLs: \href{url}{text} -> text (url), \url{url} -> url
    text = re.sub(r"\\href\{([^}]+)\}\{([^}]+)\}", r"\2 (\1)", text)
    text = re.sub(r"\\url\{([^}]+)\}", r"\1", text)

    # 5. Bullet items: \item -> • 
    text = re.sub(r"\\item\b(\[[^\]]*\])?", r"\n• ", text)

    # 6. Formatting wrappers: \textbf{...}, \textit{...}, \emph{...}, etc.
    text = re.sub(r"\\(?:textbf|textit|emph|underline|text|textsc|textsl|textsf)\{([^}]+)\}", r"\1", text)

    # 7. Strip environment wrappers: \begin{...}, \end{...}
    text = re.sub(r"\\(?:begin|end)\{[^}]+\}", "\n", text)

    # 8. Line breaks and vertical spacing macros
    text = re.sub(r"\\\\|\\newline|\\par", "\n", text)
    text = re.sub(r"\\(?:vspace|hspace|bigskip|medskip|smallskip)\*?\{[^}]*\}", "\n", text)
    text = re.sub(r"\\(?:noindent|centering|raggedright|raggedleft)\b", "", text)

    # 9. Generic macro cleaning: \cmd{content} -> content, standalone \cmd -> space
    text = re.sub(r"\\[a-zA-Z]+\*?\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)

    # 10. Unescape LaTeX special entities
    text = text.replace(r"\&", "&").replace(r"\%", "%").replace(r"\$", "$")
    text = text.replace(r"\#", "#").replace(r"\_", "_").replace(r"\{", "{").replace(r"\}", "}")
    text = text.replace("~", " ")

    # 11. Normalize whitespace and empty lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_text_from_latex(file_path: Path) -> str:
    """Extract plain text from a LaTeX (.tex) resume file"""
    try:
        raw_code = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_code = file_path.read_text(encoding="latin-1", errors="ignore")
    except Exception as e:
        raise ValueError(f"Failed to read LaTeX file: {str(e)}")

    return clean_latex_code(raw_code)


def parse_resume_content(file_path: Optional[Path] = None, file_type: str = "pdf", raw_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract clean plain text and detect contact details from:
    - PDF (.pdf)
    - Word (.docx, .doc)
    - LaTeX (.tex or pasted LaTeX code)
    - Plain Text / Markdown (.txt, .md or pasted raw text)
    """
    f_type = file_type.lower().strip().lstrip(".")

    if raw_text is not None and not file_path:
        if f_type in ["latex", "tex"]:
            text = clean_latex_code(raw_text)
        else:
            text = raw_text.strip()
    elif file_path:
        if f_type == "pdf":
            text = extract_text_from_pdf(file_path)
        elif f_type in ["docx", "doc"]:
            text = extract_text_from_docx(file_path)
        elif f_type in ["latex", "tex"]:
            text = extract_text_from_latex(file_path)
        elif f_type in ["txt", "text", "md"]:
            text = extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported resume file type: '{file_type}'. Supported: PDF, DOCX, LATEX (.tex), TXT (.txt, .md)")
    else:
        raise ValueError("Neither file_path nor raw_text was provided")

    # Safe regex extractors for contact details
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+", text)
    github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", text)

    return {
        "text": text,
        "detected_email": email_match.group(0) if email_match else "",
        "detected_phone": phone_match.group(0) if phone_match else "",
        "detected_linkedin": linkedin_match.group(0) if linkedin_match else "",
        "detected_github": github_match.group(0) if github_match else "",
    }
