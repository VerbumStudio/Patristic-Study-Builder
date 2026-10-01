def render_scene_4(draw, progress, frame):
    """Scene 4 (8.5s - 13.0s): Strategic Tradeoff Markdown Grid Output (Fixed Padding)"""
    draw_pill(draw, "STEP 2: 3-TIER TRADEOFF MATRIX", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 920
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CYAN_ACCENT, width=2)
    
    draw.text((CARD_LEFT + 40, card_y + 35), "EXECUTIVE BOUNDARY SCRIPT (OPTIONS)", font=font_h2, fill=CYAN_ACCENT)
    
    tbl_x = CARD_LEFT + 30
    tbl_y = card_y + 90
    tbl_w = CARD_WIDTH - 60
    tbl_h = 620
    
    draw_rounded_rect(draw, (tbl_x, tbl_y, tbl_x + tbl_w, tbl_y + tbl_h), radius=14, fill=CARD_HEADER_BG, outline=CYAN_ACCENT, width=2)
    
    # Rebalanced column geometry to give Column 3 adequate width
    c0 = tbl_x
    c1 = tbl_x + 190
    c2 = tbl_x + 510
    c3 = tbl_x + tbl_w
    
    draw.rectangle((c0, tbl_y, c3, tbl_y + 75), fill=(24, 45, 78))
    draw.line((c0, tbl_y + 75, c3, tbl_y + 75), fill=CYAN_ACCENT, width=2)
    draw.text((c0 + 16, tbl_y + 24), "OPTION", font=font_table_hdr, fill=CYAN_ACCENT)
    draw.text((c1 + 16, tbl_y + 24), "PROPOSED ACTION", font=font_table_hdr, fill=CYAN_ACCENT)
    draw.text((c2 + 16, tbl_y + 24), "STRATEGIC TRADEOFF", font=font_table_hdr, fill=CYAN_ACCENT)
    
    for div_x in [c1, c2]:
        draw.line((div_x, tbl_y, div_x, tbl_y + tbl_h), fill=CARD_BORDER, width=1)
        
    # Shorter strings that fit completely inside the table cell
    rows = [
        ("A: Urgent", "Ship file by 9 PM", "Delays Q4 AWS sprint 48h", ALERT_RED),
        ("B: Protect", "Deliver at 9 AM", "Zero impact to active sprint", GREEN_SAFE),
        ("C: Route", "Route to on-call", "Requires overtime sign-off", AMBER_WARN)
    ]
    
    row_y = tbl_y + 75
    row_h = 180
    for opt, act, trade, col in rows:
        draw.line((c0, row_y + row_h, c3, row_y + row_h), fill=CARD_BORDER, width=1)
        draw.text((c0 + 16, row_y + 60), opt, font=font_table_hdr, fill=col)
        draw.text((c1 + 16, row_y + 60), act, font=font_table_cell, fill=TEXT_WHITE)
        draw.text((c2 + 16, row_y + 60), trade, font=font_table_cell, fill=TEXT_MUTED)
        row_y += row_h

    badge_y = card_y + 750
    draw_rounded_rect(draw, (CARD_LEFT + 35, badge_y, CARD_RIGHT - 35, badge_y + 110), radius=16, fill=(15, 35, 55), outline=GREEN_SAFE, width=2)
    draw.text((CARD_LEFT + 70, badge_y + 25), "LEVERAGE: SENDER CHOOSES THE SACRIFICE", font=font_body_bold, fill=GREEN_SAFE)
    draw.text((CARD_LEFT + 70, badge_y + 65), "Zero emotional confrontation • Professional boundaries preserved", font=font_small, fill=TEXT_WHITE)


def render_scene_6(draw, progress, frame):
    """Scene 6 (16.5s - 20.0s): Mobile Safe-Zone Optimized End-Card with Pure Save/Bookmark Action"""
    pill_y = 380
    card_y = 460
    card_h = 950
    
    draw_pill(draw, "SAVE THIS TO PRESERVE YOUR SPRINT", 540, pill_y, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=32, fill=CARD_BG, outline=CYAN_ACCENT, width=3)
    
    draw.text((CARD_LEFT + 340, card_y + 40), "@workflowsuperai", font=font_h2, fill=CYAN_ACCENT)
    draw.text((CARD_LEFT + 70, card_y + 105), "GET THE DE-ESCALATION PROMPT", font=font_title_lg, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 220, card_y + 175), "+ FREE 7-PROMPT AI LIBRARY", font=font_h2, fill=TEXT_MUTED)
    
    term_top = card_y + 240
    term_h = 175
    draw_rounded_rect(draw, (CARD_LEFT + 40, term_top, CARD_RIGHT - 40, term_top + term_h), radius=20, fill=(10, 15, 29), outline=CYAN_ACCENT, width=2)
    draw.rounded_rectangle((CARD_LEFT + 40, term_top, CARD_RIGHT - 40, term_top + 50), radius=20, fill=CARD_HEADER_BG)
    draw.ellipse((CARD_LEFT + 65, term_top + 18, CARD_LEFT + 80, term_top + 33), fill=ALERT_RED)
    draw.ellipse((CARD_LEFT + 95, term_top + 18, CARD_LEFT + 110, term_top + 33), fill=AMBER_WARN)
    draw.ellipse((CARD_LEFT + 125, term_top + 18, CARD_LEFT + 140, term_top + 33), fill=GREEN_SAFE)
    draw.text((CARD_LEFT + 165, term_top + 14), "TERMINAL // WORKFLOW SAVE STATE", font=font_code_sm, fill=TEXT_MUTED)
    
    # Fixed spacing: added 24px gap between label and status text
    draw.text((CARD_LEFT + 80, term_top + 85), "> status:", font=font_h1, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 260, term_top + 85), "SAVED TO WORKSPACE", font=font_h1, fill=CYAN_ACCENT)
    if (frame // 8) % 2 == 0:
        draw.rectangle((CARD_LEFT + 750, term_top + 90, CARD_LEFT + 775, term_top + 130), fill=CYAN_ACCENT)

    features = [
        "✔ Bookmark this video to preserve the negotiation matrix",
        "✔ Copy prompt directly into Claude 3.5 or ChatGPT",
        "✔ Free raw markdown template available in bio"
    ]
    fy = card_y + 450
    for feat in features:
        draw.text((CARD_LEFT + 80, fy), feat, font=font_body, fill=TEXT_WHITE)
        fy += 56
        
    link_box_y = card_y + 650
    link_box_h = 240
    draw_rounded_rect(draw, (CARD_LEFT + 40, link_box_y, CARD_RIGHT - 40, link_box_y + link_box_h), radius=22, fill=(15, 23, 42), outline=CARD_BORDER, width=2)
    draw.text((CARD_LEFT + 220, link_box_y + 35), "OR ACCESS DIRECTLY VIA BEACONS:", font=font_code, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 175, link_box_y + 90), "🔗 beacons.ai/workflowsuperai", font=font_h1, fill=CYAN_ACCENT)
    
    draw_rounded_rect(draw, (CARD_LEFT + 160, link_box_y + 165, CARD_RIGHT - 160, link_box_y + 220), radius=14, fill=(28, 54, 110))
    draw.text((CARD_LEFT + 200, link_box_y + 178), "FREE 7-PROMPT AI LIBRARY IN BIO", font=font_h2, fill=TEXT_WHITE)
