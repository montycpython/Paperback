
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Image
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
from reportlab.pdfgen import canvas

class BookDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        BaseDocTemplate.__init__(self, filename, **kwargs)
        self.addPageTemplates([
            PageTemplate(
                frames=Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='normal'),
                onPage=self._add_page_number
            )
        ])
        self.actual_pages = 0  # Track total PDF pages generated

    def _add_page_number(self, canvas, doc):
        """Add page numbers starting from first content page"""
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        current_pdf_page = canvas.getPageNumber()
        self.actual_pages = max(self.actual_pages, current_pdf_page)
        
        # Start numbering from first page after copyright (page 3)
        if current_pdf_page > 2:
            displayed_number = current_pdf_page - 2
            canvas.drawCentredString(
                LETTER[0]/2.0,
                inch * 0.75,
                str(displayed_number)
            )
        canvas.restoreState()

    def afterFlowable(self, flowable):
        """Handle TOC entries with accurate page numbers"""
        if isinstance(flowable, TableOfContents):
            return  # TOC handles its own entries
        
        if hasattr(flowable, 'style') and hasattr(flowable.style, 'name'):
            if flowable.style.name in ['Chapter', 'Section']:
                # Get current PDF page number from canvas
                current_pdf_page = self.canv.getPageNumber()
                text = flowable.getPlainText()
                level = 0 if flowable.style.name == 'Chapter' else 1
                
                # Calculate displayed page number
                displayed_page = max(0, current_pdf_page - 2)
                self.notify('TOCEntry', (level, text, displayed_page))

def generate_pdf(output_path, document_data):
    """Generate complete PDF with proper structure"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    styles = getSampleStyleSheet()

    # Create custom styles
    title_style = ParagraphStyle(
        "TitlePage",
        parent=styles["Title"],
        alignment=1,
        fontSize=36,
        spaceAfter=20,
        spaceBefore=150
    )

    chapter_style = ParagraphStyle(
        "Chapter",
        parent=styles["Heading1"],
        alignment=1,
        fontSize=24,
        spaceAfter=12
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        alignment=1,
        fontSize=16,
        spaceAfter=8
    )

    # Configure Table of Contents
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            name='TOCHeading1',
            fontName='Helvetica-Bold',
            fontSize=14,
            leftIndent=20,
            spaceBefore=10
        ),
        ParagraphStyle(
            name='TOCHeading2',
            fontName='Helvetica',
            fontSize=12,
            leftIndent=40,
            spaceBefore=5
        ),
    ]

    doc = BookDocTemplate(output_path, pagesize=LETTER)
    story = []

    # Front Matter
    front = document_data.get("front_matter", [])
    if front:
        # Title Page
        story.append(Paragraph(front[0].get("title"), title_style))
        story.append(PageBreak())
        
        # Copyright Page
        if len(front) > 1:
            story.append(Paragraph(front[1].get("title"), section_style))
            for p in front[1].get("content", "").split("\n\n"):
                story += [Paragraph(p.strip(), styles["Normal"]), Spacer(1, 0.15*inch)]
            story.append(PageBreak())

    # Table of Contents
    story.append(Paragraph("Table of Contents", chapter_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(toc)
    story.append(PageBreak())

    # Remaining Front Matter
    if front and len(front) > 2:
        for section in front[2:]:
            story += process_section(section, section_style)

    # Chapters
    for chapter in document_data.get("chapters", []):
        story += process_section(chapter, chapter_style)

    # Back Matter
    for section in document_data.get("back_matter", []):
        story += process_section(section, section_style)

    # Remove final page break if exists
    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.multiBuild(story)

def process_section(section, title_style):
    """Helper to process any section with content"""
    elements = []
    if section.get("title"):
        elements.append(Paragraph(section["title"], title_style))
    
    if section.get("content"):
        for p in section["content"].split("\n\n"):
            elements += [Paragraph(p.strip(), getSampleStyleSheet()["Normal"]),
                        Spacer(1, 0.15*inch)]
    
    if section.get("images"):
        for img_path in section["images"]:
            if os.path.exists(img_path):
                elements.append(Image(img_path, width=5*inch, height=3*inch))
            else:
                elements.append(Paragraph(f"Image missing: {img_path}",
                                       getSampleStyleSheet()["Italic"]))
    
    elements.append(PageBreak())
    return elements

# Example Usage
if __name__ == "__main__":
    data = {
        "front_matter": [
            {
                "title": "How To Write Your Wrongs<br/><br/>By M.K. Jowling",
                "content": "by M.K. Jowling"
            },
            {
                "title": "Copyright Page",
                "content": """<b>Copyright</b> ©️ 2025 <br/><br/>by M.K. Jowling <br/><br/>\
All rights reserved. No part of this book may be reproduced, distributed, or transmitted in any form or by any means, \
including photocopying, recording, or other electronic or mechanical methods, without prior written permission of the publisher, except in the case of \
brief quotations embodied in critical reviews and certain other non-commercial uses permitted by copyright law. <br/><br/>\
This is a work of fiction. Names, characters, places, and incidents are the product of the author's imagination or are used fictitiously. \
Any resemblance to actual persons, living or dead, events, or locales is entirely coincidental. <br/><br/>\
Cover design by Coco Lajuan Studios <br/>
Interior design by Apollo Studios <br/>
Published by McAuthor Publishing House <br/>
First Edition: May, 2025 <br/><br/>\
Printed in the United States of America <br/><br/>\
10 9 8 7 6 5 4 3 2 1""",
                 "images": []
            },
            {
                "title": "Dedication",
                "content": "Thank you to all who supported me."
            },
            {
                "title": "Prologue",
                "content": "Thank you to all who supported me."
            }
        ],
        "chapters": [
            {
                "title": "Chapter 1: Origins",
                "content": "It all began here...\n\nWith many stories to come.",
                "images": []
            },
            {
                "title": "Chapter 2: Discovery",
                "content": "Challenges emerged.\n\nBut growth followed.",
                "images": []
            },
            {
                "title": "Chapter 3: Transformation",
                "content": "It made me <i>different.</i>\n\n I'm new now.",
                "images": []
            }
        ],
        "back_matter": [
            {
                "title": "Epilogue",
                "content": "The journey continues..."
            },
            {
                "title": "Afterword",
                "content": "Final thoughts from the author"
            },
            {
                "title": "Acknowledgments",
                "content": "Thanks to everyone involved"
            }
        ]
    }

    generate_pdf("complete_book.pdf", data)
