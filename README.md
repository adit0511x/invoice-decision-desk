# Invoice Decision Desk

Zamp AI Solutions Analyst case study, **PS-1: Invoice processing, from PDF to decision.**

The app takes a vendor invoice (a digital PDF, a scanned PDF or an image) and returns one of three decisions: **Approve**, **Hold** or **Reject**. Every reason behind the decision is visible, and every stage is logged as it runs.

**Live app:** https://adit0511x.github.io/invoice-decision-desk/

## The process

| # | Stage | What it does | Can lead to |
|---|-------|--------------|-------------|
| 1 | Receive & classify | Fingerprints the file (SHA-256). Checks whether it has a text layer, to tell a digital PDF from a scan. | — |
| 2 | Extract | Digital PDFs are read by a rule-based parser over the text layer. Scans go through OCR (Tesseract, in the browser), with the image straightened before table rows are rebuilt. When an Anthropic key is set, Claude also extracts independently, and whichever result reconciles arithmetically wins. | Hold (unreadable) |
| 3 | Validate | Checks that the invoice number, date and total are present. Rejects future dates and flags stale ones. Checks that lines + tax = total. Detects GST-inclusive pricing. | Hold |
| 4 | Vendor match | Matches on GSTIN first (allowing for 1–2 OCR character errors), then on fuzzy name. Catches unknown vendors, blocked vendors, and a matching name with a different GSTIN (impersonation risk). | Reject / Hold |
| 5 | Duplicate check | Compares the invoice number with `/ - space` stripped against the ledger and earlier runs. Also checks for an identical file fingerprint, and for the same amount from the same vendor within 45 days. | Reject / Hold |
| 6 | Find PO | Uses the printed PO, read in any format. If none is printed, infers it from the vendor's open POs by line-item similarity, but only when one PO clearly wins. | Hold |
| 7 | 3-way match | For each line: compares billed quantity with goods received minus quantity already invoiced, and billed rate with the PO rate (pre-tax). Also compares the invoice total with the PO-derived amount. | Hold |
| 8 | Decide | Produces the decision, reasons, next steps, the amount that can be part-approved, and a draft vendor message. Approval posts to the PO and the ledger. | Approve / Hold / Reject |

**Decision policy.** *Reject* means "never pay this": a duplicate, an unknown vendor or a blocked vendor. *Hold* means a person must decide: a price change, over-billing, missing data, or an amount above the touchless limit. *Approve* happens only when every check passes. The system never silently pays something doubtful.

## Edge cases (in `invoices/`)

1. **Split PO over-billing (BrightPath).** This is the second running bill on a 20-trip freight PO. The PO shows 18 trips received, and 12 were already billed on the first invoice. This invoice bills 10 → **Hold**. It suggests part-approving ₹2,83,200 for the 6 trips that are both delivered and unbilled.
2. **No PO number, GST-inclusive pricing (Coreline).** The vendor has two open POs. The PO is inferred from the line items, and prices are converted to pre-tax before comparison → **Approve**, flagged "PO inferred".
3. **Disguised duplicate (Apex re-send).** A "Reminder: payment due" copy of a paid invoice, re-dated, with the number printed as `INV/AS/1152` instead of `INV-AS-1152` → **Reject**.
4. **Scanned invoice with a silent price increase (Delta).** The PDF is a slightly rotated phone scan with no text layer. OCR reads it; Claude vision reads it instead if a key is set. OCR misreads the GSTIN (`…Q121` instead of `…Q1Z1`), and the vendor match tolerates that and records it. Paper is billed at ₹1,450 against the PO rate of ₹1,300 (+11.5%) → **Hold**. The buyer is asked to confirm the price.

Re-running the happy path after it was approved is rejected as a duplicate, which is a quick live demo of state.

## Assumptions

- Indian GST context, amounts in ₹. Dates are read as DD-MM-YYYY.
- Tolerances: unit price ±2%; invoice total ±1% capped at ₹2,500. Clean invoices above ₹5,00,000 still need Finance Controller sign-off. All of these can be edited live in *Rules & settings*.
- The PO, goods-receipt and ledger data are a small in-browser dataset (see *Vendors & POs*). In production this would come from the ERP.

## Running it

It's a single static page with no server. Open `index.html`, or use the GitHub Pages link.

- **No key needed.** Digital PDFs use the rule-based parser, and scans use free in-browser OCR.
- **Optional:** add an Anthropic API key in *Rules & settings* to have Claude read the invoices too, as a cross-check, and read scans with vision. The key is stored only in the browser and is sent only to `api.anthropic.com`.

Stack: vanilla JS, pdf.js (text layer + rendering), Tesseract.js (OCR), the optional Anthropic Messages API (`claude-haiku-5-5` for text, `claude-sonnet-5-5` for vision), and localStorage for run history. `gen.py` regenerates the test invoices and reference data.

## What I'd build next

- Email inbox ingestion.
- ERP connectors for live PO and GRN data.
- An approval workflow with roles.
- Vendor bank-detail change detection.
- Learning per-vendor layouts from corrections.
