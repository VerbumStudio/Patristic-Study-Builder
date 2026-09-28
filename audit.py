"""
AUDIT ENGINE: DETERMINISTIC LAYOUT, SAFE-ZONE & TYPOGRAPHY VERIFIER
"""

# Screen & Safe-Zone Geometry (1080 x 1920)
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 1920
SAFE_Y_MIN = 380      # Above this collides with TikTok top navigation & search
SAFE_Y_MAX = 1550     # Below this collides with description, audio & CTA UI
MIN_CARD_BUFFER = 70  # Minimum vertical separation between elements
MAX_CHARS_PER_LINE = 42

def run_layout_audit(layout_config):
    """
    Evaluates vertical coordinate compliance and element separation.
    Returns: (bool passed, list[str] errors)
    """
    errors = []
    
    pill_y = layout_config.get("pill_y", 0)
    card_top = layout_config.get("card_top", 0)
    card_bottom = layout_config.get("card_bottom", 0)
    
    # 1. Safe Zone Margin Verification
    if pill_y < SAFE_Y_MIN:
        errors.append(f"Top pill at Y={pill_y} violates top safe boundary (minimum {SAFE_Y_MIN}px).")
        
    if card_bottom > SAFE_Y_MAX:
        errors.append(f"Card bottom at Y={card_bottom} exceeds bottom safe boundary (maximum {SAFE_Y_MAX}px).")
        
    # 2. Collision Guardrail
    buffer = card_top - pill_y
    if buffer < MIN_CARD_BUFFER:
        errors.append(f"Element collision: separation between pill and card is {buffer}px (requires >={MIN_CARD_BUFFER}px).")
        
    # 3. Line Length & Typography Overflow
    lines = layout_config.get("lines", [])
    for idx, line in enumerate(lines):
        if len(line) > MAX_CHARS_PER_LINE:
            errors.append(f"Line {idx + 1} overflow: {len(line)} characters (maximum recommended is {MAX_CHARS_PER_LINE}).")
            
    return (len(errors) == 0, errors)
