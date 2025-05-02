from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Image
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
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
        self.actual_pages = 0

    def _add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        current_pdf_page = canvas.getPageNumber()
        self.actual_pages = max(self.actual_pages, current_pdf_page)
        if current_pdf_page > 2:
            displayed_number = current_pdf_page - 2
            canvas.drawCentredString(LETTER[0]/2.0, inch * 0.75, str(displayed_number))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, TableOfContents):
            return
        if hasattr(flowable, 'style') and hasattr(flowable.style, 'name'):
            if getattr(flowable, '_no_toc', False):
                return
            if flowable.style.name in ['Chapter', 'Section']:
                current_pdf_page = self.canv.getPageNumber()
                text = flowable.getPlainText()
                level = 0 if flowable.style.name == 'Chapter' else 1
                displayed_page = max(0, current_pdf_page - 2)
                self.notify('TOCEntry', (level, text, displayed_page))

def generate_pdf(output_path, document_data):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("TitlePageTitle", parent=styles["Title"], alignment=1, fontSize=28, spaceAfter=0.2 * inch)
    subtitle_style = ParagraphStyle("TitlePageSubtitle", parent=styles["Normal"], alignment=1, fontSize=18, spaceAfter=0.1 * inch)
    author_style = ParagraphStyle("TitlePageAuthor", parent=styles["Normal"], alignment=1, fontSize=16, spaceAfter=0.3 * inch)
    publisher_style = ParagraphStyle("TitlePagePublisher", parent=styles["Normal"], alignment=1, fontSize=14, spaceAfter=0.2 * inch)
    chapter_style = ParagraphStyle("Chapter", parent=styles["Heading1"], alignment=1, fontSize=28, spaceAfter=12)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], alignment=1, fontSize=22, spaceAfter=8)
    centered_normal = ParagraphStyle("CenteredNormal", parent=styles["Normal"], alignment=1, spaceAfter=0.2*inch)

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(name='TOCHeading1', fontName='Helvetica-Bold', fontSize=20, leftIndent=20, spaceBefore=10),
        ParagraphStyle(name='TOCHeading2', fontName='Helvetica', fontSize=12, leftIndent=40, spaceBefore=5),
    ]

    doc = BookDocTemplate(output_path, pagesize=LETTER)
    story = []

    front = document_data.get("front_matter", [])
    if front:
        title_data = front[0]
        title_elements = [Paragraph(title_data.get("title"), title_style)]
        if title_data.get("subtitle"):
            title_elements.append(Paragraph(title_data.get("subtitle"), subtitle_style))
        if title_data.get("author"):
            title_elements.append(Paragraph(title_data.get("author"), author_style))
        if title_data.get("publisher"):
            title_elements.append(Paragraph(title_data.get("publisher"), publisher_style))
        image_element = None
        if "images" in title_data and title_data["images"] and os.path.exists(title_data["images"][0]):
            img = Image(title_data["images"][0], width=2*inch, height=1*inch, hAlign='CENTER')
            image_element = img
        elif "images" in title_data and title_data["images"]:
            title_elements.append(Paragraph(f"Image missing: {title_data['images'][0]}", getSampleStyleSheet()["Italic"]))

        temp_canvas = canvas.Canvas('temp.pdf')
        available_height = LETTER[1] - doc.topMargin - doc.bottomMargin
        elements_height = sum(el.wrapOn(temp_canvas, LETTER[0], LETTER[1])[1] for el in title_elements)
        if image_element:
            elements_height += image_element.wrapOn(temp_canvas, LETTER[0], LETTER[1])[1]
        temp_canvas.save()

        remaining_space = available_height - elements_height
        top_spacer_height = remaining_space * 0.3
        middle_spacer_height = remaining_space * 0.4
        bottom_spacer_height = remaining_space * 0.3

        story.append(Spacer(1, top_spacer_height))
        for element in title_elements[:-1]:
            story.append(element)
            story.append(Spacer(1, middle_spacer_height / (len(title_elements) + (1 if image_element else 0))))
        if image_element:
            story.append(image_element)
            story.append(Spacer(1, middle_spacer_height / (len(title_elements) + 1)))
        story.append(title_elements[-1])
        story.append(Spacer(1, bottom_spacer_height))

        # Removed PageBreak() after the title page to avoid the extra blank page
        # story.append(PageBreak())

        if len(front) > 1:
            copyright_data = front[1]
            copyright_title = Paragraph(copyright_data.get("title"), section_style)
            copyright_title._no_toc = True

            temp_canvas = canvas.Canvas('temp.pdf')
            available_height = LETTER[1] - doc.topMargin - doc.bottomMargin
            content_paragraphs = []
            total_height = 0
            for p in copyright_data.get("content", "").split("<br/><br/>"):
                para = Paragraph(p.strip(), centered_normal)
                para._no_toc = True
                para_height = para.wrapOn(temp_canvas, LETTER[0], LETTER[1])[1] + 0.1 * inch
                total_height += para_height
                content_paragraphs.append((para, para_height))
            temp_canvas.save()

            remaining_space = available_height - total_height - copyright_title.wrapOn(temp_canvas, LETTER[0], LETTER[1])[1]
            top_spacer_height = max(0, remaining_space / 2)
            story.append(Spacer(1, top_spacer_height))
            story.append(copyright_title)
            for para, _ in content_paragraphs:
                story.append(para)
            story.append(PageBreak())

    story.append(Paragraph("Table of Contents", chapter_style))
    story[-1]._no_toc = True
    story.append(Spacer(1, 0.2*inch))
    toc._no_toc = True
    story.append(toc)
    story.append(PageBreak())

    if front and len(front) > 2:
        for section in front[2:]:
            story += process_section(section, section_style)

    for chapter in document_data.get("chapters", []):
        story += process_section(chapter, chapter_style)

    for section in document_data.get("back_matter", []):
        story += process_section(section, section_style)

    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.multiBuild(story)

def process_section(section, title_style):
    elements = []
    if section.get("title"):
        para = Paragraph(section["title"], title_style)
        para._no_toc = False
        elements.append(para)
    if section.get("images"):
        for img_path in section["images"]:
            if os.path.exists(img_path):
                elements.append(Image(img_path, width=5*inch, height=3*inch))
            else:
                elements.append(Paragraph(f"Image missing: {img_path}", getSampleStyleSheet()["Italic"]))
    if section.get("content"):
        for p in section["content"].split("\n\n"):
            elements += [Paragraph(p.strip(), getSampleStyleSheet()["Normal"]), Spacer(1, 0.15*inch)]
    elements.append(PageBreak())
    return elements

if __name__ == "__main__":
    data = {
        "front_matter": [
            {
                "title": "How To <i>Write</i> Your Wrongs:",
                "subtitle": "Realize Your Respect, Rights, and Royalties",
                "author": "M.K. Jowling",
                "publisher": "McAuthor Publishing House",
                "images": ["/content/drive/My Drive/assets/McAuthor.jpg"]
            },
            {
                "title": "Copyright ©️2025",
                "content": """<br/><br/>by M.K. Jowling <br/><br/>
All rights reserved. No part of this book may be reproduced, distributed, or transmitted in any form or by any means,
including photocopying, recording, or other electronic or mechanical methods, without prior written permission of the publisher, except in the case of
brief quotations embodied in critical reviews and certain other non-commercial uses permitted by copyright law. <br/><br/>
This is a work of fiction. Names, characters, places, and incidents are the product of the author's imagination or are used fictitiously.
Any resemblance to actual persons, living or dead, events, or locales is entirely coincidental. <br/><br/>
Cover design by Coco Lajuan Studios <br/>
Interior design by Apollo Studios <br/>
Published by McAuthor Publishing House <br/>
First Edition: May, 2025 <br/><br/>
Printed in the United States of America <br/><br/>
10 9 8 7 6 5 4 3 2 1"""
            },
            {
                "title": "Dedication",
                "content": """Thank you to all who <i>supported</i> me.\
\n\n<p>To the homeless.</p><br/><br/><p>To the abandoned.</p>"""
            },
            {
                "title":"Foreword",
                "content":"What's the main idea?"
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
            },
            {
                "title": "Chapter 4: Travel",
                "content": """Go far away. <br/><b>Go very far away.</b>""",
                "images": []
            },
            {
                "title": "Chapter 5: New Beginnings",
                "content": "Test...\n\nWith many stories to come.",
                "images": []
            },
            {
                "title": "Chapter 6: Realize",
                "content": "Yesterday.\n\nBut growth followed.",
                "images": []
            },
            {
                "title": "Chapter 7: Renew",
                "content": "Love <i>is</i> different.\n\n I'm new now.",
                "images": []
            },
            {
                "title": "Chapter 8: Journey",
                "content": """Go far away. <br/><b>Go very far away.</b>Again.""",
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
                "content": "Thanks to everyone involved",
                "images": ["/content/drive/My Drive/assets/paperbackapp.jpg"]
            }
        ]
    }

    generate_pdf("/content/drive/My Drive/pythondev/write_your_wrongs_book.pdf", data)
