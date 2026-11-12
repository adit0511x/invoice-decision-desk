"""Generates the procurement reference data and the five test invoice PDFs."""
import json, os, random
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = os.path.join(os.path.dirname(__file__), "invoices")
os.makedirs(OUT, exist_ok=True)
W, H = A4

BUYER = {"name": "Northwind Manufacturing Pvt Ltd", "gstin": "27AAACN4455P1Z3",
         "address": "Plot 14, MIDC Bhosari, Pune 411026"}

VENDORS = [
    {"id": "V-1001", "name": "Apex Steel Supplies Pvt Ltd", "gstin": "27AABCA1234F1Z5", "terms": "Net 30", "status": "active", "aliases": ["Apex Steel"]},
    {"id": "V-1002", "name": "BrightPath Logistics LLP", "gstin": "07AAJFB5678K1Z2", "terms": "Net 15", "status": "active", "aliases": ["BrightPath"]},
    {"id": "V-1003", "name": "Coreline Electricals", "gstin": "09AAFFC4321M1Z8", "terms": "Net 30", "status": "active", "aliases": ["Coreline"]},
    {"id": "V-1004", "name": "Delta Office Solutions", "gstin": "29AADCD8765Q1Z1", "terms": "Net 45", "status": "active", "aliases": ["Delta Office"]},
    {"id": "V-1005", "name": "Evergreen Packaging Industries", "gstin": "24AACCE2468R1Z4", "terms": "Net 30", "status": "active", "aliases": []},
    {"id": "V-1006", "name": "Nimbus IT Services", "gstin": "29AAGCN1357T1Z6", "terms": "Net 30", "status": "blocked", "aliases": [], "note": "Suspended after bank-detail mismatch, Sep 2026"},
]

def line(sku, desc, qty, price, recv=None, inv=0, unit="nos"):
    return {"sku": sku, "desc": desc, "unit": unit, "qty": qty, "unit_price": price,
            "qty_received": qty if recv is None else recv, "qty_invoiced": inv}

POS = [
    {"po": "PO-2026-0398", "vendor_id": "V-1001", "date": "2026-09-22", "status": "closed", "tax_rate": 18,
     "lines": [line("MA-40-5", "MS Angle 40x40x5mm", 80, 960, inv=80)]},
    {"po": "PO-2026-0412", "vendor_id": "V-1001", "date": "2026-10-14", "status": "open", "tax_rate": 18,
     "lines": [line("RB-12", "MS Round Bar 12mm", 40, 4250), line("FL-50-6", "MS Flat 50x6mm", 60, 1180),
               line("SVC-CH", "Cutting & handling charges", 1, 6500, unit="lot")]},
    {"po": "PO-2026-0377", "vendor_id": "V-1002", "date": "2026-09-02", "status": "open", "tax_rate": 18,
     "lines": [line("FTL-PUN-CHE", "FTL freight Pune to Chennai (32ft MXL)", 20, 38500, recv=18, inv=12, unit="trips"),
               line("LU-CHG", "Loading / unloading charges", 20, 1500, recv=18, inv=12, unit="trips")]},
    {"po": "PO-2026-0421", "vendor_id": "V-1003", "date": "2026-10-20", "status": "open", "tax_rate": 18,
     "lines": [line("LED-2X2-40", "LED panel light 2x2 40W", 120, 1350), line("MCB-32-DP", "MCB 32A double pole", 60, 640)]},
    {"po": "PO-2026-0433", "vendor_id": "V-1003", "date": "2026-10-28", "status": "open", "tax_rate": 18,
     "lines": [line("CAB-4C-16", "Armoured cable 4C x 16 sq mm", 300, 410, unit="m"), line("GL-25", "Cable gland 25mm", 100, 85)]},
    {"po": "PO-2026-0450", "vendor_id": "V-1004", "date": "2026-10-30", "status": "open", "tax_rate": 18,
     "lines": [line("CH-ERG", "Ergonomic office chair", 25, 6800), line("PAP-A4-75", "A4 copier paper 75gsm (box of 5 reams)", 40, 1300, unit="box"),
               line("WB-4X3", "Whiteboard 4x3 ft", 6, 2450)]},
    {"po": "PO-2026-0455", "vendor_id": "V-1005", "date": "2026-11-02", "status": "open", "tax_rate": 18,
     "lines": [line("CB-5PLY", "5-ply corrugated box 18x12x12", 2000, 46)]},
]

LEDGER = [
    {"invoice_no": "INV-AS-1152", "vendor_id": "V-1001", "po": "PO-2026-0398", "date": "2026-10-08", "total": 90624.0, "status": "Paid", "paid_on": "2026-11-06"},
    {"invoice_no": "INV-BPL-0741", "vendor_id": "V-1002", "po": "PO-2026-0377", "date": "2026-10-15", "total": 566400.0, "status": "Paid", "paid_on": "2026-10-29"},
    {"invoice_no": "EPI/2026/311", "vendor_id": "V-1005", "po": "PO-2026-0302", "date": "2026-08-19", "total": 64900.0, "status": "Paid", "paid_on": "2026-09-18"},
]

def inr(x):
    s = f"{x:,.2f}"
    # Indian grouping
    whole, dec = s.replace(",", "").split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    return f"{whole}.{dec}"

# ---------- 1. Apex Steel — happy path ----------
def apex(path, inv_no, inv_date, po, items, stamp=None, ref_label="P.O. No."):
    c = canvas.Canvas(path, pagesize=A4)
    c.setFillColor(colors.HexColor("#1f3b57")); c.rect(0, H - 90, W, 90, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 20); c.drawString(40, H - 50, "Apex Steel Supplies Pvt Ltd")
    c.setFont("Helvetica", 9); c.drawString(40, H - 68, "Gat No. 221, Chakan Industrial Area, Pune 410501  |  GSTIN: 27AABCA1234F1Z5")
    c.setFont("Helvetica-Bold", 16); c.drawRightString(W - 40, H - 50, "TAX INVOICE")
    c.setFillColor(colors.black); c.setFont("Helvetica", 10)
    y = H - 120
    for k, v in [("Invoice No.", inv_no), ("Invoice Date", inv_date), (ref_label, po), ("Payment Terms", "Net 30")]:
        c.drawString(360, y, f"{k}:"); c.drawString(460, y, v); y -= 15
    c.setFont("Helvetica-Bold", 10); c.drawString(40, H - 120, "Bill To")
    c.setFont("Helvetica", 10); c.drawString(40, H - 135, BUYER["name"]); c.drawString(40, H - 150, BUYER["address"])
    c.drawString(40, H - 165, "GSTIN: " + BUYER["gstin"])
    y = H - 210
    c.setFillColor(colors.HexColor("#e8eef4")); c.rect(40, y - 5, W - 80, 18, fill=1, stroke=0); c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    for x, t in [(45, "#"), (65, "Description"), (300, "HSN"), (350, "Qty"), (410, "Rate"), (490, "Amount")]:
        c.drawString(x, y, t)
    c.setFont("Helvetica", 9); y -= 20; sub = 0
    for i, (desc, hsn, q, r) in enumerate(items, 1):
        amt = q * r; sub += amt
        c.drawString(45, y, str(i)); c.drawString(65, y, desc); c.drawString(300, y, hsn)
        c.drawString(350, y, str(q)); c.drawString(410, y, inr(r)); c.drawRightString(W - 45, y, inr(amt)); y -= 16
    tax = round(sub * 0.18, 2); cg = round(tax / 2, 2)
    y -= 10; c.line(330, y + 8, W - 40, y + 8)
    for k, v in [("Taxable Value", sub), ("CGST @ 9%", cg), ("SGST @ 9%", tax - cg)]:
        c.drawString(350, y, k); c.drawRightString(W - 45, y, inr(v)); y -= 15
    c.setFont("Helvetica-Bold", 11); c.drawString(350, y - 4, "Grand Total (INR)"); c.drawRightString(W - 45, y - 4, inr(sub + tax))
    c.setFont("Helvetica", 8); c.drawString(40, 80, "Bank: HDFC Bank, Chakan  |  A/c ending 4471  |  IFSC HDFC0001234")
    c.drawString(40, 68, "This is a computer generated invoice.")
    if stamp:
        c.saveState(); c.setFillColor(colors.HexColor("#c0392b")); c.setFont("Helvetica-Bold", 30)
        c.translate(330, 330); c.rotate(20); c.drawString(0, 0, stamp); c.restoreState()
    c.save()
    return sub + tax

t1 = apex(f"{OUT}/01_happy_apex_INV-AS-1203.pdf", "INV-AS-1203", "05-11-2026", "PO-2026-0412",
          [("MS Round Bar 12mm", "7214", 40, 4250), ("MS Flat 50x6mm", "7211", 60, 1180), ("Cutting & handling charges", "9988", 1, 6500)])

# ---------- 4. Apex duplicate re-send of INV-AS-1152 ----------
t4 = apex(f"{OUT}/04_edge_duplicate_apex_resend.pdf", "INV/AS/1152", "10-11-2026", "PO 2026 0398",
          [("MS Angle 40x40x5mm", "7216", 80, 960)], stamp="REMINDER - PAYMENT DUE", ref_label="Your Order Ref")

# ---------- 2. BrightPath — split PO over-billing ----------
def brightpath(path):
    c = canvas.Canvas(path, pagesize=A4)
    c.setFont("Helvetica-Bold", 18); c.drawString(40, H - 55, "BRIGHTPATH LOGISTICS LLP")
    c.setFont("Helvetica", 9); c.drawString(40, H - 70, "Khasra 45, Samalkha, New Delhi 110037  -  GSTIN 07AAJFB5678K1Z2")
    c.setStrokeColor(colors.HexColor("#f39c12")); c.setLineWidth(3); c.line(40, H - 80, W - 40, H - 80)
    c.setFont("Helvetica-Bold", 12); c.drawString(40, H - 105, "Invoice")
    c.setFont("Helvetica", 10)
    rows = [("Bill No:", "INV-BPL-0778"), ("Dated:", "07 Nov 2026"), ("Purchase Order:", "PO-2026-0377"),
            ("Customer:", BUYER["name"]), ("Period:", "Trips completed 16 Oct - 06 Nov 2026 (2nd running bill)")]
    y = H - 125
    for k, v in rows:
        c.drawString(40, y, k); c.drawString(140, y, v); y -= 15
    y -= 15; c.setFont("Helvetica-Bold", 9)
    for x, t in [(40, "Service description"), (330, "Trips"), (390, "Rate/trip"), (500, "Value")]:
        c.drawString(x, y, t)
    c.setFont("Helvetica", 9); y -= 18; sub = 0
    for desc, q, r in [("FTL freight Pune to Chennai (32ft MXL)", 10, 38500), ("Loading / unloading charges", 10, 1500)]:
        amt = q * r; sub += amt
        c.drawString(40, y, desc); c.drawString(330, y, str(q)); c.drawString(390, y, inr(r)); c.drawRightString(W - 45, y, inr(amt)); y -= 16
    tax = sub * 0.18; y -= 12
    for k, v in [("Sub-total", sub), ("IGST 18%", tax)]:
        c.drawString(390, y, k); c.drawRightString(W - 45, y, inr(v)); y -= 15
    c.setFont("Helvetica-Bold", 11); c.drawString(390, y - 4, "Amount Payable"); c.drawRightString(W - 45, y - 4, inr(sub + tax))
    c.setFont("Helvetica", 8); c.drawString(40, 70, "Previous running bill: INV-BPL-0741 (12 trips). Kindly remit within 15 days.")
    c.save(); return sub + tax

t2 = brightpath(f"{OUT}/02_edge_split_po_overbill_brightpath.pdf")

# ---------- 3. Coreline — no PO ref, GST-inclusive pricing ----------
def coreline(path):
    c = canvas.Canvas(path, pagesize=A4)
    c.setFont("Times-Bold", 22); c.drawCentredString(W / 2, H - 55, "Coreline Electricals")
    c.setFont("Times-Roman", 10); c.drawCentredString(W / 2, H - 70, "B-17 Sector 63, Noida, Uttar Pradesh 201301")
    c.drawCentredString(W / 2, H - 83, "GSTIN 09AAFFC4321M1Z8   |   accounts@coreline.example")
    c.setFont("Times-Bold", 13); c.drawCentredString(W / 2, H - 110, "TAX INVOICE")
    c.setFont("Times-Roman", 10)
    c.drawString(40, H - 135, "Invoice Number: CE/26-27/0912"); c.drawRightString(W - 40, H - 135, "Invoice Date: 2026-11-04")
    c.drawString(40, H - 150, "Buyer: " + BUYER["name"] + ", Pune"); c.drawRightString(W - 40, H - 150, "Dispatch: Truck UP16 KT 2210")
    c.drawString(40, H - 165, "Order reference: as per telephonic confirmation")
    y = H - 200; c.setFont("Times-Bold", 10)
    for x, t in [(40, "Sl"), (65, "Item"), (330, "Quantity"), (400, "Unit Rate"), (500, "Total")]:
        c.drawString(x, y, t)
    c.line(40, y - 4, W - 40, y - 4); c.setFont("Times-Roman", 10); y -= 20; tot = 0
    for i, (d, q, r) in enumerate([("LED Panel 2x2 ft 40 Watt", 120, 1593.00), ("MCB 32 Amp DP", 60, 755.20)], 1):
        amt = round(q * r, 2); tot += amt
        c.drawString(40, y, f"{i}."); c.drawString(65, y, d); c.drawString(330, y, str(q)); c.drawString(400, y, inr(r)); c.drawRightString(W - 45, y, inr(amt)); y -= 16
    y -= 10; c.line(330, y + 8, W - 40, y + 8)
    c.setFont("Times-Bold", 11); c.drawString(400, y - 4, "Invoice Total"); c.drawRightString(W - 45, y - 4, inr(tot))
    c.setFont("Times-Italic", 9); c.drawString(40, y - 30, "All rates are inclusive of GST @ 18%. E. & O.E.")
    c.save(); return tot

t3 = coreline(f"{OUT}/03_edge_no_po_tax_inclusive_coreline.pdf")

# ---------- 5. Delta Office — scanned image, price variance ----------
def delta_scan(path):
    S = 2  # render scale
    img = Image.new("L", (int(W * S), int(H * S)), 250)
    d = ImageDraw.Draw(img)
    fdir = "/usr/share/fonts/truetype/dejavu/"
    F = lambda sz, b=False: ImageFont.truetype(fdir + ("DejaVuSans-Bold.ttf" if b else "DejaVuSans.ttf"), sz * S)
    def txt(x, y, s, sz=10, b=False, right=False):
        f = F(sz, b)
        if right: x = x - d.textlength(s, font=f) / S
        d.text((x * S, y * S), s, fill=30, font=f)
    txt(40, 40, "DELTA OFFICE SOLUTIONS", 18, True)
    txt(40, 64, "No. 8, 2nd Cross, Peenya Industrial Area, Bengaluru 560058")
    txt(40, 78, "GSTIN: 29AADCD8765Q1Z1")
    txt(W - 40, 40, "INVOICE", 16, True, right=True)
    txt(360, 110, "Invoice #: DOS-26-4471"); txt(360, 125, "Date: 06/11/2026"); txt(360, 140, "PO Number: PO-2026-0450")
    txt(40, 110, "Sold to:", 10, True); txt(40, 125, BUYER["name"]); txt(40, 140, BUYER["address"])
    y = 185; d.rectangle([40 * S, (y - 4) * S, (W - 40) * S, (y + 14) * S], outline=60, width=2)
    for x, t in [(45, "Item"), (330, "Qty"), (390, "Unit Price"), (490, "Amount")]:
        txt(x, y, t, 10, True)
    y += 24; sub = 0
    for dsc, q, r in [("Ergonomic office chair (mesh back)", 25, 6800), ("A4 copier paper 75gsm - box of 5 reams", 40, 1450), ("Whiteboard 4x3 ft magnetic", 6, 2450)]:
        amt = q * r; sub += amt
        txt(45, y, dsc); txt(330, y, str(q)); txt(390, y, inr(r)); txt(W - 45, y, inr(amt), right=True); y += 18
    tax = sub * 0.18; y += 12
    for k, v in [("Subtotal", sub), ("IGST @ 18%", tax)]:
        txt(390, y, k); txt(W - 45, y, inr(v), right=True); y += 16
    txt(390, y + 4, "TOTAL DUE", 11, True); txt(W - 45, y + 4, inr(sub + tax), 11, True, right=True)
    txt(40, 760, "Thank you for your business. Payment within 45 days.", 9)
    # make it look scanned: rotate, blur, noise
    img = img.rotate(-0.8, fillcolor=235, expand=False).filter(ImageFilter.GaussianBlur(0.7))
    random.seed(7); px = img.load()
    for _ in range(60000):
        x, y2 = random.randrange(img.width), random.randrange(img.height)
        px[x, y2] = max(0, min(255, px[x, y2] + random.randint(-40, 25)))
    png = path.replace(".pdf", ".jpg"); img.convert("RGB").save(png, quality=55)
    c = canvas.Canvas(path, pagesize=A4); c.drawImage(png, 0, 0, W, H); c.save(); os.remove(png)
    return sub + tax

t5 = delta_scan(f"{OUT}/05_edge_scanned_price_variance_delta.pdf")

json.dump({"buyer": BUYER, "vendors": VENDORS, "pos": POS, "ledger": LEDGER},
          open(os.path.join(os.path.dirname(__file__), "refdata.json"), "w"), indent=1)
print("totals", t1, t2, t3, t4, t5)
