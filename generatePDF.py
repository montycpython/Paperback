from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os

def generate_pdf(output_path, chapters):
    # Create the document
    doc = SimpleDocTemplate(output_path, pagesize=LETTER)
    styles = getSampleStyleSheet()
    
    story = []

    for chapter in chapters:
        title = chapter.get("title", "Untitled Chapter")
        content = chapter.get("content", "")
        images = chapter.get("images", [])

        # Chapter Title
        story.append(Paragraph(f"<b>{title}</b>", styles["Heading1"]))
        story.append(Spacer(1, 0.25 * inch))

        # Chapter Content
        for paragraph in content.split("\n\n"):
            story.append(Paragraph(paragraph.strip(), styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # Chapter Images
        for img_path in images:
            if os.path.exists(img_path):
                img = Image(img_path, width=5*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 0.25 * inch))
            else:
                story.append(Paragraph(f"<i>Image not found: {img_path}</i>", styles["Normal"]))

        # Page break after each chapter
        story.append(PageBreak())

    # Build the document
    doc.build(story)

# Example usage
if __name__ == "__main__":
    chapters_data = [
        {
            "title": "Chapter 1: The Beginning",
            "content": "This is the first chapter.\n\nIt contains multiple paragraphs of text.",
            "images": ["example1.jpg"]
        },
        {
            "title": "Chapter 2: The Next Step",
            "content": "This is the second chapter.\n\nMore details and developments.",
            "images": ["example2.jpg"]
        }
    ]

    generate_pdf("longform_document.pdf", chapters_data)
