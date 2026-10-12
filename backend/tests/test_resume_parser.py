import pytest
from pathlib import Path
from backend.app.services.resume_parser import clean_latex_code, parse_resume_content


def test_latex_resume_cleaning():
    latex_sample = r"""
\documentclass[letterpaper,11pt]{article}
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\begin{document}

% Personal Header comment
\textbf{\Huge Jane Doe} \\
\href{mailto:jane.doe@example.com}{jane.doe@example.com} $|$ (555) 345-6789 $|$ \url{https://github.com/janedoe}

\section{Experience}
\textbf{Senior Software Engineer} -- Acme Cloud \hfill 2022 -- Present \\
\begin{itemize}
    \item Architected high-throughput microservices using Python \& FastAPI.
    \item Decreased query latency by 45\% through query optimization and Redis caching.
\end{itemize}

\section{Skills}
\textbf{Languages:} Python, TypeScript, SQL, Go \\
\textbf{Frameworks:} React, FastAPI, Docker, Kubernetes

\end{document}
"""
    cleaned = clean_latex_code(latex_sample)
    
    # Assert macros and environments are stripped
    assert r"\documentclass" not in cleaned
    assert r"\begin{document}" not in cleaned
    assert r"\end{document}" not in cleaned
    assert r"\textbf" not in cleaned
    assert r"\section" not in cleaned
    
    # Assert content and entities are preserved and unescaped
    assert "Jane Doe" in cleaned
    assert "jane.doe@example.com" in cleaned
    assert "• Architected high-throughput microservices using Python & FastAPI." in cleaned
    assert "45%" in cleaned  # Unescaped from \%
    assert "Languages: Python, TypeScript, SQL, Go" in cleaned


def test_parse_resume_content_latex(tmp_path):
    tex_file = tmp_path / "resume.tex"
    tex_file.write_text(r"""
\begin{document}
John Developer \\
Email: john.dev@test.org $|$ Phone: (555) 987-6543 $|$ https://github.com/johndev
\section{Summary}
Experienced Python engineer with 6 years experience.
\end{document}
""", encoding="utf-8")

    parsed = parse_resume_content(file_path=tex_file, file_type="tex")
    assert "John Developer" in parsed["text"]
    assert parsed["detected_email"] == "john.dev@test.org"
    assert parsed["detected_phone"] == "(555) 987-6543"
    assert "github.com/johndev" in parsed["detected_github"]


def test_parse_resume_content_text(tmp_path):
    txt_file = tmp_path / "resume.txt"
    txt_file.write_text("""
Alice Smith
Email: alice.smith@corp.com | Phone: 555-123-4567 | linkedin.com/in/alicesmith
Summary: Full Stack Developer specializing in React and Node.js.
Skills: JavaScript, TypeScript, React, Tailwind CSS, PostgreSQL
""", encoding="utf-8")

    parsed = parse_resume_content(file_path=txt_file, file_type="txt")
    assert "Alice Smith" in parsed["text"]
    assert parsed["detected_email"] == "alice.smith@corp.com"
    assert "alicesmith" in parsed["detected_linkedin"]


def test_api_resume_paste_endpoint(client):
    payload = {
        "label": "Test LaTeX Resume",
        "target_categories": ["Backend", "Python"],
        "is_primary": False,
        "file_type": "tex",
        "content": r"""
\begin{document}
Alex Mercer
alex.mercer@test.com
\section{Skills}
Python, FastAPI, Docker
\end{document}
"""
    }
    res = client.post("/api/v1/profile/resumes/paste", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["label"] == "Test LaTeX Resume"
    assert data["file_type"] == "tex"
    assert "Alex Mercer" in data["extracted_text"]
    assert "Python, FastAPI, Docker" in data["extracted_text"]
