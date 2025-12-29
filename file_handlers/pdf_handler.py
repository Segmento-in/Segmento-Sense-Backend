import fitz  # PyMuPDF
import io

class PdfHandler:
    def __init__(self, ocr_engine):
        """
        :param ocr_engine: Instance of OcrEngine to handle scanned pages.
        """
        self.ocr_engine = ocr_engine
        print("✅ PDF Handler loaded.")

    def get_total_pages(self, file_bytes: bytes) -> int:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            return len(doc)
        except:
            return 0

    def get_page_text(self, file_bytes: bytes, page_num: int) -> str:
        """
        Extracts text from a specific page. Falls back to OCR if text is empty.
        """
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            if not (0 <= page_num < len(doc)): return ""
            
            page = doc[page_num]
            text = page.get_text("text")
            
            # OCR Fallback for scanned PDFs
            if not text.strip() and self.ocr_engine.available:
                print(f"⚠️ Page {page_num+1} appears empty/scanned. Running OCR...")
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                text = self.ocr_engine.extract_text(img_bytes)
                
            return text
        except Exception as e:
            print(f"PDF Text Error: {e}")
            return ""

    def render_labeled_image(self, file_bytes: bytes, page_num: int, matches: list, color_map: dict) -> bytes:
        """
        Draws bounding boxes around detected PII on the PDF page image.
        """
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            if not (0 <= page_num < len(doc)): return None
            
            page = doc[page_num]
            
            # Draw rectangles for each match
            for m in matches:
                # Get color for this PII type (normalize 0-255 rgb to 0-1 for PyMuPDF)
                # color_map values are hex strings or tuples. Assuming the backend passes hex or we default.
                # Simplification: Use Red for all boxes for visibility, or logic below:
                color_norm = (1, 0, 0) # Default Red
                
                # Search for the text string on the page
                quads = page.search_for(m['text'])
                
                for q in quads:
                    # Draw Box
                    page.draw_rect(q, color=color_norm, width=1.5, fill=color_norm, fill_opacity=0.2)
                    # Add Label
                    page.insert_text(fitz.Point(q.x0, q.y0-2), m['label'], fontsize=6, color=(0,0,0))
            
            # Render page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom=2 for higher quality
            return pix.tobytes("png")
            
        except Exception as e:
            print(f"PDF Render Error: {e}")
            return None