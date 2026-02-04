"""
PDF Text Extraction Service
Extracts text content from policy PDFs using pdfplumber
"""

import logging
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of PDF text extraction"""
    success: bool
    text: str
    page_count: int
    pages: List[Dict]  # Per-page text with metadata
    tables: List[Dict]  # Extracted tables
    error: Optional[str] = None


class PDFExtractor:
    """
    Extracts text and tables from policy PDF documents.

    Uses pdfplumber for high-quality text extraction with layout preservation.
    """

    def __init__(self):
        self.min_text_threshold = 500  # Minimum chars for valid extraction

    async def extract_from_file(self, file_path: str) -> ExtractionResult:
        """
        Extract all text content from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            ExtractionResult with extracted text and metadata
        """
        logger.info(f"📄 Starting PDF extraction: {file_path}")

        if not os.path.exists(file_path):
            return ExtractionResult(
                success=False,
                text="",
                page_count=0,
                pages=[],
                tables=[],
                error=f"File not found: {file_path}"
            )

        try:
            pages = []
            tables = []
            full_text = []

            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                logger.info(f"   PDF has {page_count} pages")

                for i, page in enumerate(pdf.pages):
                    page_num = i + 1

                    # Extract text
                    text = page.extract_text() or ""
                    full_text.append(f"--- Page {page_num} ---\n{text}")

                    pages.append({
                        "page_number": page_num,
                        "text": text,
                        "char_count": len(text),
                    })

                    # Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        for j, table in enumerate(page_tables):
                            if table:  # Non-empty table
                                tables.append({
                                    "page": page_num,
                                    "table_index": j,
                                    "rows": table,
                                })

                    # Progress logging
                    if page_num % 10 == 0:
                        logger.info(f"   Processed {page_num}/{page_count} pages")

            combined_text = "\n\n".join(full_text)
            total_chars = len(combined_text)

            logger.info(f"✅ Extraction complete: {total_chars} chars, {len(tables)} tables")

            # Quality check
            if total_chars < self.min_text_threshold:
                logger.warning(f"⚠️ Low text extraction ({total_chars} chars) - may need OCR")

            return ExtractionResult(
                success=True,
                text=combined_text,
                page_count=page_count,
                pages=pages,
                tables=tables,
            )

        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {str(e)}")
            return ExtractionResult(
                success=False,
                text="",
                page_count=0,
                pages=[],
                tables=[],
                error=str(e)
            )

    async def extract_from_url(self, url: str, temp_dir: str = "temp") -> ExtractionResult:
        """
        Download PDF from URL and extract text.

        Args:
            url: Presigned URL to download PDF
            temp_dir: Directory for temporary file storage

        Returns:
            ExtractionResult with extracted text
        """
        import aiohttp
        import uuid

        logger.info(f"📥 Downloading PDF from URL")

        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"download_{uuid.uuid4().hex[:8]}.pdf")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return ExtractionResult(
                            success=False,
                            text="",
                            page_count=0,
                            pages=[],
                            tables=[],
                            error=f"Failed to download PDF: HTTP {response.status}"
                        )

                    content = await response.read()
                    with open(temp_path, "wb") as f:
                        f.write(content)

            logger.info(f"   Downloaded {len(content)} bytes")

            # Extract from downloaded file
            result = await self.extract_from_file(temp_path)

            # Cleanup temp file
            try:
                os.remove(temp_path)
            except:
                pass

            return result

        except Exception as e:
            logger.error(f"❌ Download/extraction failed: {str(e)}")
            return ExtractionResult(
                success=False,
                text="",
                page_count=0,
                pages=[],
                tables=[],
                error=str(e)
            )


# Module-level instance for convenience
extractor = PDFExtractor()
