import os
import sys
from PIL import ImageFont

# ==============================================================================
# AUDIT HARNESS: DETERMINISTIC LAYOUT & SAFE-ZONE VERIFIER
# ==============================================================================

SAFE_Y_MIN = 380
SAFE_Y_MAX = 1550
MAX_LINE_LENGTH = 45

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def run_audit(data_dict):
    """
    Checks layout parameters, text bounding boundaries, and character constraints.
    Returns: (bool passed, list errors)
    """
    errors = []
    
    # 1. Safe Zone Margin Verification
    pill_y = data_dict.get("pill_y", 0)
    card_top = data_dict.get("card_top", 0)
    card_bottom = data_dict.get("card_bottom", 0)
    
    if pill_y < SAFE_Y_MIN:
        errors.append(f"Safe-Zone Violation: Top pill at Y={pill_y} sits above safe limit ({SAFE_Y_MIN}px).")
        
    if card_bottom > SAFE_Y_MAX:
        errors.append(f"Safe-Zone Violation: Terminal card ends at Y={card_bottom}, exceeding bottom limit ({SAFE_Y_MAX}px).")
        
    # 2. Collision Guardrail (Top Pill vs Card Container)
    buffer = card_top - pill_y
    if buffer < 70:
        errors.append(f"Element Collision: Buffer between pill and card is {buffer}px (minimum safe buffer is 70px).")
        
    # 3. Text Overflow Verification
    lines = data_dict.get("lines", [])
    for idx, line in enumerate(lines):
        if len(line) > MAX_LINE_LENGTH:
            errors.append(f"Text Overflow: Line {idx+1} has {len(line)} chars (max recommended is {MAX_LINE_LENGTH}).")
            
    passed = len(errors) == 0
    return passed, errors

if __name__ == "__main__":
    # Test stub verifying syntax integrity
    sample_data = {
        "pill_y": 380,
        "card_top": 460,
        "card_bottom": 1540,
        "lines": ["Clean test line within safe limits."]
    }
    ok, errs = run_audit(sample_data)
    if ok:
        print("VERIFIER CHECK: PASSED (Geometry valid)")
        sys.exit(0)
    else:
        print("VERIFIER CHECK: FAILED\n" + "\n".join(errs))
        sys.exit(1)
