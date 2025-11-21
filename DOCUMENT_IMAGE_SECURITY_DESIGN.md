# Document & Image Security Design

## Overview

This document outlines the design decision and implementation approach for sanitizing images and documents (PDFs, Word docs) that may contain sensitive information before sending to OpenAI's API.

**Status**: Design Phase
**Decision Required**: Choose between 3 approaches outlined below
**Target Implementation**: Phase 2/3

---

## Problem Statement

### Current State (Phase 1)

**What's Protected:**
- ✅ PDF text extraction with code block removal
- ✅ Word document text extraction with code block removal
- ✅ Text file sanitization (code blocks removed)

**What's NOT Protected:**
- ❌ Images (screenshots, UI mockups, diagrams) may contain:
  - Company branding and logos
  - Internal URLs and email addresses
  - Employee names in screenshots
  - Database schemas in architecture diagrams
  - API endpoints and internal IPs
  - Customer data in mockups
  - OCR-readable text with PII

- ❌ Embedded images in PDFs/Word docs
- ❌ Scanned documents (images of text)

### Risk Assessment

**High-Risk Image Types:**
1. **Screenshots** - May show internal dashboards, URLs, user emails
2. **Architecture Diagrams** - Database schemas, API endpoints, IP addresses
3. **UI Mockups** - May contain test customer data, internal URLs
4. **Scanned Documents** - May be contracts, forms with PII
5. **Error Messages** - Stack traces, file paths, credentials

**Medium-Risk Image Types:**
1. **Wireframes** - Usually safe but may have internal terminology
2. **Flowcharts** - May reference internal systems
3. **Data Models** - May show sensitive table/field names

**Low-Risk Image Types:**
1. **Generic icons** - Usually safe
2. **Stock photos** - Safe
3. **Abstract diagrams** - Usually safe

---

## Approach Options

### Option 1: OCR + Pixel-Level Redaction (High Security, High Complexity)

**How It Works:**
1. Extract text from images using OCR (Tesseract/EasyOCR)
2. Apply same PII detection used for text (emails, IPs, API keys)
3. Calculate pixel coordinates of detected entities
4. Redact pixels using black boxes or blur
5. Send sanitized image to OpenAI

**Technology Stack:**
- **OCR**: Tesseract-OCR or EasyOCR
- **Image Processing**: Pillow (PIL) or OpenCV
- **PII Detection**: Microsoft Presidio (already used for text)

**Pros:**
- ✅ Preserves most image context (UI layout, colors, structure)
- ✅ Precise redaction of only sensitive areas
- ✅ Works with all image types (screenshots, diagrams, mockups)
- ✅ Reuses existing PII detection logic
- ✅ OpenAI can still analyze non-sensitive visual elements

**Cons:**
- ❌ Complex implementation (OCR → PII detection → pixel mapping → redaction)
- ❌ May miss stylized text or text in unusual fonts
- ❌ OCR can be slow (1-3 seconds per image)
- ❌ Requires additional dependencies (tesseract, opencv)
- ❌ Coordinate mapping can be tricky (OCR bounding boxes may be inaccurate)

**Implementation Complexity:** HIGH (5-7 days)

**Example Workflow:**
```python
# Pseudocode for Option 1
def sanitize_image_with_ocr(image_path: str) -> bytes:
    # 1. Load image
    image = Image.open(image_path)

    # 2. Extract text with coordinates
    ocr_data = pytesseract.image_to_data(image, output_type=Output.DICT)

    # 3. Detect PII in extracted text
    text = " ".join(ocr_data['text'])
    pii_entities = presidio_analyzer.analyze(text, entities=["EMAIL", "IP_ADDRESS", "PHONE"])

    # 4. Map PII entities back to pixel coordinates
    redaction_boxes = map_entities_to_pixels(pii_entities, ocr_data)

    # 5. Draw black boxes over sensitive regions
    draw = ImageDraw.Draw(image)
    for box in redaction_boxes:
        draw.rectangle(box, fill="black")

    # 6. Return sanitized image bytes
    return image_to_bytes(image)
```

**Dependencies:**
```bash
pip install pytesseract pillow opencv-python
# Also requires system install: apt-get install tesseract-ocr (Linux) or brew install tesseract (Mac)
```

---

### Option 2: Local Vision Model "Describe & Block" (Balanced Security, Medium Complexity)

**How It Works:**
1. Use local vision model (LLaVA, BLIP-2) to generate text description of image
2. Send text description to OpenAI instead of actual image
3. Block original image entirely
4. Optionally sanitize the description text before sending

**Technology Stack:**
- **Local Vision Models**:
  - LLaVA (7B or 13B) - Open source, runs locally
  - BLIP-2 - Salesforce model, open source
  - MiniGPT-4 - Lightweight alternative
- **Inference**: Hugging Face Transformers or LlamaIndex

**Pros:**
- ✅ No sensitive pixels sent to OpenAI (highest security)
- ✅ OpenAI still gets semantic understanding via description
- ✅ Descriptions can be sanitized using existing text sanitizer
- ✅ Works for all image types
- ✅ No coordinate mapping complexity

**Cons:**
- ❌ Loses visual context (colors, layouts, exact UI elements)
- ❌ Requires GPU for reasonable inference speed (or slow CPU inference)
- ❌ Large model downloads (LLaVA 7B = ~13GB)
- ❌ May hallucinate details not in image
- ❌ Descriptions may miss important visual details
- ❌ Adds significant latency (2-5 seconds per image on GPU, 10-30s on CPU)

**Implementation Complexity:** MEDIUM (3-5 days)

**Example Workflow:**
```python
# Pseudocode for Option 2
def sanitize_image_with_local_model(image_path: str) -> str:
    # 1. Load local vision model (one-time initialization)
    model = load_local_vision_model("llava-7b")

    # 2. Generate description
    image = Image.open(image_path)
    description = model.generate_caption(
        image,
        prompt="Describe this UI mockup/diagram in detail, focusing on functional elements."
    )

    # 3. Sanitize description text (remove any PII that slipped through)
    sanitized_description = sanitize_text(description)

    # 4. Return description instead of image
    return sanitized_description
```

**Example Transformation:**
- **Original Image**: Screenshot showing "Login to https://internal.company.com/admin" with admin@company.com
- **Description**: "A login screen with username and password fields. A URL field shows an internal domain. An email input field is visible."
- **Sanitized Description**: "A login screen with username and password fields. A URL field shows an internal domain. An email input field is visible."

**Dependencies:**
```bash
pip install transformers torch pillow accelerate
# Model download: ~13GB for LLaVA-7B
```

**Hardware Requirements:**
- **Minimum**: 16GB RAM, CPU inference (slow)
- **Recommended**: GPU with 8GB+ VRAM for reasonable speed

---

### Option 3: Complete Blur/Block (Maximum Security, Minimal Complexity)

**How It Works:**
1. Replace entire image with placeholder text or blurred version
2. Send only functional metadata to OpenAI (filename, file type, dimensions)
3. Do not send any visual content

**Technology Stack:**
- Minimal - just Pillow for blur (if providing blurred version)
- Or no dependencies if just blocking entirely

**Pros:**
- ✅ Simplest implementation (1-2 hours)
- ✅ Highest security guarantee (zero pixels sent)
- ✅ No dependencies or complexity
- ✅ Fast (no processing needed)
- ✅ No hallucination risk

**Cons:**
- ❌ OpenAI loses ALL visual context
- ❌ Cannot analyze UI layouts, mockups, diagrams
- ❌ Significantly degrades AI quality for visual requirements
- ❌ User experience suffers (why upload images if they're ignored?)

**Implementation Complexity:** LOW (1-2 hours)

**Example Workflow:**
```python
# Pseudocode for Option 3
def sanitize_image_complete_block(image_path: str) -> Dict[str, Any]:
    # Option A: Return only metadata
    return {
        "type": "image_blocked",
        "filename": os.path.basename(image_path),
        "note": "[IMAGE BLOCKED FOR SECURITY - Contains potential sensitive visual data]"
    }

    # Option B: Return blurred version (still risky if text visible)
    image = Image.open(image_path)
    blurred = image.filter(ImageFilter.GaussianBlur(radius=20))
    return image_to_bytes(blurred)
```

**Use Cases:**
- High-security environments where NO visual data can leave premises
- Temporary solution until OCR or local model approach is implemented
- Fallback for images flagged as high-risk

---

## Comparison Matrix

| Criteria | Option 1: OCR + Redaction | Option 2: Local Vision Model | Option 3: Complete Block |
|----------|---------------------------|------------------------------|--------------------------|
| **Security Level** | High (redacts PII only) | Highest (no pixels sent) | Highest (no content sent) |
| **AI Quality Impact** | Low (preserves visuals) | Medium (loses layout) | High (loses all context) |
| **Implementation Time** | 5-7 days | 3-5 days | 1-2 hours |
| **Dependencies** | Tesseract, OpenCV, Pillow | Transformers, Torch (~13GB) | Pillow (optional) |
| **Runtime Performance** | Medium (1-3s/image) | Slow (2-30s/image) | Fast (<0.1s/image) |
| **Hardware Requirements** | CPU only | GPU recommended | None |
| **Maintenance Burden** | Medium | Medium-High | Low |
| **False Positives** | Low (precise redaction) | Low (description level) | N/A (blocks all) |
| **User Experience** | Good (preserves mockups) | Fair (descriptions only) | Poor (no visuals) |

---

## Recommended Approach: Hybrid Strategy

**Recommendation**: Implement a **tiered approach** that combines all three options based on image risk level and user preference.

### Tier 1: Low-Risk Images (Option 1 - OCR + Redaction)
- Apply to: Generic wireframes, simple mockups, flowcharts
- Benefit: Preserves visual context for AI analysis
- Fallback: If OCR fails, use Tier 2

### Tier 2: Medium-Risk Images (Option 2 - Local Vision Model)
- Apply to: Screenshots, architecture diagrams, complex mockups
- Benefit: Semantic understanding without exposing pixels
- Fallback: If model unavailable, use Tier 3

### Tier 3: High-Risk Images (Option 3 - Complete Block)
- Apply to: Images detected with credentials, customer data, legal documents
- Benefit: Maximum security for sensitive content
- Manual override: User can choose to force Tier 3 for any image

### Configuration System

Allow users to set security level:

```python
class ImageSecurityLevel(Enum):
    LOW = "low"           # Use OCR + Redaction for all
    MEDIUM = "medium"     # Use Local Vision Model for screenshots, OCR for diagrams
    HIGH = "high"         # Use Local Vision Model for all
    MAXIMUM = "maximum"   # Block all images completely

# Configuration in settings
IMAGE_SECURITY_LEVEL = ImageSecurityLevel.MEDIUM
```

### Implementation Priority

**Phase 2 (Immediate - Week 2-3):**
1. Implement Option 3 (Complete Block) as default
   - Fast to implement, maximum security
   - Provides immediate protection while building better solutions

2. Add configuration toggle to allow users to opt-in to image processing

**Phase 3 (Future - Week 4-6):**
1. Implement Option 1 (OCR + Redaction) for opt-in users
   - Better AI quality, still secure
   - Test with internal users first

2. Implement Option 2 (Local Vision Model) as alternative
   - For users with GPU resources
   - Highest security with semantic understanding

**Phase 4 (Long-term - Month 2+):**
1. Build risk classifier to auto-select tier
2. Add user preview showing redacted/described images
3. Collect metrics on sanitization effectiveness

---

## Implementation Details

### Phase 2: Complete Block (Default)

**File**: `src/ai_tester/utils/data_sanitizer.py`

```python
def sanitize_image_attachment(attachment: Dict[str, Any], security_level: str = "maximum") -> Dict[str, Any]:
    """
    Sanitize image attachment based on security level.

    Args:
        attachment: Attachment dict with 'content', 'filename', 'type'
        security_level: "low", "medium", "high", or "maximum"

    Returns:
        Sanitized attachment (may be blocked, redacted, or described)
    """
    if security_level == "maximum":
        # Block completely
        return {
            "type": "image_blocked",
            "filename": attachment.get("filename", "unknown.png"),
            "original_type": attachment.get("type", "image"),
            "note": "[IMAGE BLOCKED FOR SECURITY]",
            "message": "Image contains potential sensitive visual data and has been blocked from AI analysis."
        }

    # Future: Implement "high" (local model), "medium" (OCR + redaction), "low" (OCR only)
    else:
        raise NotImplementedError(f"Security level '{security_level}' not yet implemented. Only 'maximum' is available.")
```

**Integration Point**: `src/ai_tester/clients/jira_client.py` (line ~238-243)

Current code:
```python
# Apply sanitization if enabled
if self.enable_sanitization:
    result = sanitize_attachment(result, remove_code=True)
    print(f"DEBUG: Sanitized attachment: {filename}")
```

Updated code:
```python
# Apply sanitization if enabled
if self.enable_sanitization:
    # Text-based attachments: sanitize text content
    if result.get('type') in ['document', 'text']:
        result = sanitize_attachment(result, remove_code=True)
        print(f"DEBUG: Sanitized attachment: {filename}")

    # Image attachments: apply image security
    elif result.get('type') == 'image':
        result = sanitize_image_attachment(result, security_level=self.image_security_level)
        print(f"DEBUG: Image security applied to: {filename}")
```

**Configuration**: Add to `JiraClient.__init__`:
```python
def __init__(
    self,
    base_url: str,
    email: str,
    api_token: str,
    enable_sanitization: bool = True,
    sanitizer_config: Optional[FieldWhitelistConfig] = None,
    image_security_level: str = "maximum"  # NEW
):
    ...
    self.image_security_level = image_security_level
```

---

### Phase 3: OCR + Redaction (Opt-in)

**Dependencies:**
```bash
pip install pytesseract pillow opencv-python
```

**New File**: `src/ai_tester/utils/image_sanitizer.py`

```python
"""
Image sanitization utilities for redacting sensitive information from images.
"""
from typing import Dict, List, Tuple, Any
import re
from PIL import Image, ImageDraw
import pytesseract
from presidio_analyzer import AnalyzerEngine

class ImageSanitizer:
    """Sanitizes images using OCR + PII detection + pixel redaction"""

    def __init__(self):
        self.analyzer = AnalyzerEngine()

    def sanitize_image_with_ocr(self, image_path: str) -> bytes:
        """
        Extract text via OCR, detect PII, redact sensitive regions.

        Args:
            image_path: Path to image file

        Returns:
            Sanitized image as bytes
        """
        # 1. Load image
        image = Image.open(image_path)

        # 2. OCR with bounding boxes
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        # 3. Detect PII in text
        full_text = " ".join(ocr_data['text'])
        pii_results = self.analyzer.analyze(
            text=full_text,
            entities=["EMAIL_ADDRESS", "IP_ADDRESS", "PHONE_NUMBER", "URL"],
            language="en"
        )

        # 4. Map PII entities to pixel coordinates
        redaction_boxes = self._map_entities_to_boxes(pii_results, ocr_data)

        # 5. Draw black rectangles over sensitive regions
        draw = ImageDraw.Draw(image)
        for box in redaction_boxes:
            draw.rectangle(box, fill="black")

        # 6. Return sanitized image
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def _map_entities_to_boxes(
        self,
        pii_results: List[Any],
        ocr_data: Dict[str, List]
    ) -> List[Tuple[int, int, int, int]]:
        """
        Map PII entity character offsets to pixel bounding boxes.

        Returns:
            List of (left, top, right, bottom) tuples for redaction
        """
        boxes = []

        # Build character offset to bounding box mapping from OCR data
        char_offset = 0
        word_boxes = []
        for i, text in enumerate(ocr_data['text']):
            if text.strip():
                word_boxes.append({
                    'text': text,
                    'start': char_offset,
                    'end': char_offset + len(text),
                    'left': ocr_data['left'][i],
                    'top': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i]
                })
                char_offset += len(text) + 1  # +1 for space

        # For each PII entity, find overlapping words and get their bounding boxes
        for entity in pii_results:
            entity_start = entity.start
            entity_end = entity.end

            # Find all words that overlap with this entity
            for word_box in word_boxes:
                if (word_box['start'] <= entity_end and word_box['end'] >= entity_start):
                    # Calculate bounding box with padding
                    left = word_box['left'] - 5
                    top = word_box['top'] - 5
                    right = left + word_box['width'] + 10
                    bottom = top + word_box['height'] + 10
                    boxes.append((left, top, right, bottom))

        return boxes
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_image_sanitizer.py

def test_image_complete_block():
    """Test that images are blocked when security level is maximum"""
    attachment = {
        "type": "image",
        "filename": "screenshot.png",
        "content": b"fake_image_bytes"
    }

    result = sanitize_image_attachment(attachment, security_level="maximum")

    assert result["type"] == "image_blocked"
    assert result["filename"] == "screenshot.png"
    assert "BLOCKED" in result["message"]
    assert "content" not in result  # No image bytes included

def test_ocr_redaction_email():
    """Test that emails in images are redacted"""
    # Create test image with email text
    test_image = create_test_image_with_text("Contact: admin@company.com")

    sanitizer = ImageSanitizer()
    sanitized_bytes = sanitizer.sanitize_image_with_ocr(test_image)

    # OCR the sanitized image
    sanitized_image = Image.open(io.BytesIO(sanitized_bytes))
    extracted_text = pytesseract.image_to_string(sanitized_image)

    # Email should be redacted (unreadable)
    assert "admin@company.com" not in extracted_text
```

### Integration Tests

```python
# tests/test_jira_image_security.py

def test_jira_attachment_image_security():
    """Test that Jira image attachments are sanitized"""
    jira_client = JiraClient(
        base_url=JIRA_URL,
        email=JIRA_EMAIL,
        api_token=JIRA_TOKEN,
        enable_sanitization=True,
        image_security_level="maximum"
    )

    # Mock attachment with image
    attachment = {
        "filename": "mockup.png",
        "content": {"url": "https://jira.company.com/attachment/12345"}
    }

    result = jira_client.process_attachment("PROJ-123", attachment)

    # Should be blocked
    assert result["type"] == "image_blocked"
    assert "content" not in result or result["content"] == ""
```

---

## Decision Required

**Immediate Action (Phase 2 - This Week):**
1. Implement **Option 3 (Complete Block)** as default
2. Add configuration parameter `image_security_level="maximum"`
3. Update documentation to inform users images are blocked for security

**Future Enhancement (Phase 3 - Next Month):**
1. Implement **Option 1 (OCR + Redaction)** for users who opt-in
2. Add GPU detection and offer **Option 2 (Local Vision Model)** if GPU available
3. Build risk classifier to auto-select best approach per image

**Recommendation**: Start with Option 3 (maximum security, minimal complexity), then incrementally add Option 1 and Option 2 as opt-in features based on user feedback and security review.

---

## Next Steps

1. ✅ Review this design document with security team
2. ⏳ Get approval for Phase 2 implementation (Complete Block)
3. ⏳ Implement `sanitize_image_attachment()` in `data_sanitizer.py`
4. ⏳ Update `jira_client.py` to use image sanitization
5. ⏳ Add configuration parameter for image security level
6. ⏳ Test with real Jira attachments
7. ⏳ Update user documentation
8. ⏳ Plan Phase 3 implementation (OCR + Redaction)

---

## References

- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)
- [Microsoft Presidio - PII Detection](https://microsoft.github.io/presidio/)
- [LLaVA - Large Language and Vision Assistant](https://llava-vl.github.io/)
- [Pillow (PIL) - Image Processing](https://pillow.readthedocs.io/)
- [OpenCV - Computer Vision Library](https://opencv.org/)
