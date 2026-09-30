def run_layout_audit(config):
    errors = []
    pill_y = config.get("pill_y", 380)
    card_top = config.get("card_top", 460)
    card_bottom = config.get("card_bottom", 1540)

    if pill_y < 380:
        errors.append(f"pill_y ({pill_y}) must be >= 380")
    if card_bottom > 1550:
        errors.append(f"card_bottom ({card_bottom}) must be <= 1550")
    if (card_top - pill_y) < 70:
        errors.append(f"Card buffer ({card_top - pill_y}) must be >= 70")

    passed = len(errors) == 0
    return passed, errors

def run_audit(config):
    return run_layout_audit(config)
