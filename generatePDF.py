from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, Image, PageBreak, TableOfContents
)
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os

class ChapterTrackingDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.chapter_title = ""

        frame = Frame(
            self.leftMargin, self.bottomMargin,
            self.width, self.height - 0.5 * inch,
            id='normal'
        )
        template = PageTemplate(id='default', frames=frame,
                                onPage=self.add_header_footer)
        self.addPageTemplates([template])

    def afterFlowable(self, flowable):
        """Track chapter titles for TOC and header."""
        if isinstance(flowable, Paragraph):
            style_name = flowable.style.name
            text = flowable.getPlainText()

            if style_name == "Heading1":
                self.chapter_title = text
                self.notify('TOCEntry', (0, text, self.page))

            elif style_name == "Heading2":
                self.notify('TOCEntry', (1, text, self.page))

    def add_header_footer(self, canvas, doc):
        canvas.saveState()
        width, height = LETTER

        # Header: current chapter
        if self.chapter_title:
            canvas.setFont('Helvetica-Oblique', 9)
            canvas.drawString(doc.leftMargin, height - 0.5 * inch, self.chapter_title)

        # Footer: page number
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(width - doc.rightMargin, 0.5 * inch, f"Page {doc.page}")
        canvas.restoreState()


def generate_pdf(output_path, document_data):
    doc = ChapterTrackingDocTemplate(output_path, pagesize=LETTER)
    styles = getSampleStyleSheet()

    # Custom style for centered title page
    title_style = ParagraphStyle(
        "TitlePage",
        parent=styles["Title"],
        alignment=1,  # center
        fontSize=24,
        spaceAfter=20,
        spaceBefore=150
    )

    story = []

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(fontName='Helvetica-Bold', fontSize=14, name='TOCHeading1', leftIndent=20, spaceBefore=10),
        ParagraphStyle(fontName='Helvetica', fontSize=12, name='TOCHeading2', leftIndent=40, spaceBefore=5),
    ]

    story.append(Paragraph("Table of Contents", styles["Heading1"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(toc)
    story.append(PageBreak())

    def add_sections(sections, is_chapter=False, center_title=False):
        for section in sections:
            title = section.get("title", "Untitled")
            content = section.get("content", "")
            images = section.get("images", [])

            heading_style = styles["Heading1"] if is_chapter else styles["Heading2"]
            if center_title:
                story.append(Paragraph(title, title_style))
            else:
                story.append(Paragraph(title, heading_style))
            story.append(Spacer(1, 0.25 * inch))

            for paragraph in content.split("\n\n"):
                story.append(Paragraph(paragraph.strip(), styles["Normal"]))
                story.append(Spacer(1, 0.15 * inch))

            for img_path in images:
                if os.path.exists(img_path):
                    img = Image(img_path, width=5 * inch, height=3 * inch)
                    story.append(img)
                    story.append(Spacer(1, 0.25 * inch))
                else:
                    story.append(Paragraph(f"<i>Image not found: {img_path}</i>", styles["Normal"]))

            story.append(PageBreak())

    # Front Matter
    front = document_data.get("front_matter", [])
    if front:
        # Treat the first front-matter item as title page
        first = front[0]
        add_sections([first], is_chapter=False, center_title=True)
        if len(front) > 1:
            add_sections(front[1:], is_chapter=False)

    # Chapters
    add_sections(document_data.get("chapters", []), is_chapter=True)

    # Back Matter
    add_sections(document_data.get("back_matter", []), is_chapter=False)

    doc.build(story)

# ✅ Example
if __name__ == "__main__":
    data = {
        "front_matter": [
            {
                "title": "How To Write Your Wrongs\n\nBy M.K. Jowling",
                "content": ""  # Title page has no body
            },
            {
                "title": "Copyright Page",
                "content": """<b>Copyright</b> ©️ 2025 by M.K. Jowling <br/><br/>\
All rights reserved. No part of this book may be reproduced, distributed, or transmitted in any form or by any means, \
including photocopying, recording, or other electronic or mechanical methods, without prior written permission of the publisher, except in the case of \
brief quotations embodied in critical reviews and certain other non-commercial uses permitted by copyright law. <br/><br/>\
This is a work of fiction. Names, characters, places, and incidents are the product of the author's imagination or are used fictitiously. \
Any resemblance to actual persons, living or dead, events, or locales is entirely coincidental. <br/><br/>\
Cover design by Coco Lajuan Studios <br/>\
Interior design by Apollo Studios <br/>\
Published by McAuthor Publishing House <br/>\
First Edition: April, 2025 <br/><br/>\
Printed in the United States of America <br/><br/>\
10 9 8 7 6 5 4 3 2 1"""
            },
            {
                "title": "Dedication",
                "content": "Thank you to all who supported me."
            },
            {
                "title": "Foreword",
                "content": "To those who inspire."
            },
            {
                "title": "Prologue",
                "content": "To those who inspire."
            }
        ],
        "chapters": [
            {
                "title": "Chapter 1: Origins",
                "content": "It all began here...\n\nWith many stories to come.",
                "images": ["example1.jpg"]
            },
            {
                "title": "Chapter 2: Discovery",
                "content": "Challenges emerged.\n\nBut growth followed.",
                "images": ["example2.jpg"]
            }
        ],
        "back_matter": [
            {
                "title": "Epilogue",
                "content": "Supplemental data and technical notes."
            },
            {
                "title": "Afterword",
                "content": "Supplemental data and technical notes."
            },
            {
                "title": "Acknowledgments",
                "content": "The Creator of the Universe and all who supported me."
            }
        ]
    }

    generate_pdf("longform_book_final.pdf", data)
