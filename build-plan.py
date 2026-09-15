"""
Builds the Ordo task plan PDF — what to do next, and how.

    python docs/build-plan.py

English deliberately: ReportLab's built-in fonts carry no Sinhala glyphs, so
Sinhala would render as black boxes without an embedded font. The codebase,
comments and column names are English too, so this reads alongside the code
without switching languages.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

INK = colors.HexColor("#12211f")
SOFT = colors.HexColor("#5b6b68")
BRAND = colors.HexColor("#0f3d3e")
ACCENT = colors.HexColor("#b4530a")
LINE = colors.HexColor("#dfe5e3")
BG = colors.HexColor("#f6f8f7")

base = getSampleStyleSheet()["Normal"]


def st(name, **kw):
    return ParagraphStyle(name, parent=base, **kw)


S = {
    "title": st("t", fontName="Helvetica-Bold", fontSize=26, leading=30,
                textColor=BRAND, spaceAfter=4),
    "sub": st("s", fontSize=11, leading=15, textColor=SOFT, spaceAfter=16),
    "task": st("tk", fontName="Helvetica-Bold", fontSize=14, leading=18,
               textColor=BRAND, spaceBefore=16, spaceAfter=2),
    "why": st("w", fontSize=9.5, leading=13, textColor=SOFT, spaceAfter=8),
    "lbl": st("l", fontName="Helvetica-Bold", fontSize=9, leading=12,
              textColor=ACCENT, spaceBefore=6, spaceAfter=3),
    "body": st("b", fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=5),
    "bul": st("bu", fontSize=9.5, leading=13.5, textColor=INK,
              leftIndent=12, bulletIndent=2, spaceAfter=2),
    "code": st("c", fontName="Courier", fontSize=7.8, leading=10.5,
               textColor=INK, backColor=BG, borderPadding=5,
               leftIndent=3, spaceBefore=3, spaceAfter=7),
    "note": st("n", fontSize=9, leading=12.5, textColor=ACCENT, spaceAfter=7),
    "cell": st("cl", fontSize=8.3, leading=11, textColor=INK),
    "cellh": st("ch", fontName="Helvetica-Bold", fontSize=8.3, leading=11,
                textColor=colors.white),
}

story = []
P = lambda t: story.append(Paragraph(t, S["body"]))
LBL = lambda t: story.append(Paragraph(t, S["lbl"]))
NOTE = lambda t: story.append(Paragraph(t, S["note"]))
GAP = lambda h=6: story.append(Spacer(1, h))


def CODE(t):
    story.append(Paragraph(
        t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
         .replace(" ", "&nbsp;").replace("\n", "<br/>"), S["code"]))


def BUL(items):
    for i in items:
        story.append(Paragraph(i, S["bul"], bulletText="•"))
    GAP(4)


def TASK(n, title, why):
    story.append(Paragraph(f"Task {n} — {title}", S["task"]))
    story.append(Paragraph(why, S["why"]))


def TABLE(headers, rows, widths):
    data = [[Paragraph(h, S["cellh"]) for h in headers]]
    data += [[Paragraph(str(c), S["cell"]) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    GAP(8)


# ------------------------------------------------------------------ header
story.append(Paragraph("Ordo — what to build next", S["title"]))
story.append(Paragraph(
    "Eight tasks in order, each with the technical work it requires. "
    "Ordered by risk retired per day, not by interest.", S["sub"]))

TABLE(
    ["#", "Task", "Depends on"],
    [
        ["0", "Verify order capture against a live database", "Docker restored"],
        ["1", "Measure reply latency (50 real replies)", "Task 0"],
        ["2", "Two safe latency fixes", "Task 1"],
        ["3", "Variants and stock-accurate answers", "—"],
        ["4", "Finish the order loop: Today, notify, stock check", "Tasks 0, 3"],
        ["5", "Per-conversation memory", "—"],
        ["6", "Images in chat", "—"],
        ["7", "Rule-based fast path", "Task 1 data"],
    ],
    [8 * mm, 100 * mm, 58 * mm],
)

NOTE("Task 0 is first because the order-capture code is written and type-checked "
     "but has never run against Postgres or a real conversation. Nothing built on "
     "top of it can be trusted until it is proven.")

# No page break here — Task 0 flows onto page 1 rather than leaving it half empty.

# ------------------------------------------------------------------ 0
TASK(0, "Verify order capture end to end",
     "The multi-turn order flow exists in code with 23 passing unit tests, but "
     "the database half has never executed. Prove it before adding anything.")

LBL("Technical work")
BUL([
    "Restore Docker, then <font face='Courier'>docker compose up -d</font> and "
    "<font face='Courier'>npm run migrate</font> (11 migrations, none new).",
    "Drive a real conversation through WhatsApp: item, name, phone, address, "
    "then “ow hari”.",
    "Assert in the database, not in the UI, at each turn.",
])

LBL("Checks")
CODE("""-- draft accumulates, does not reset
SELECT state, customer_name, phone, address,
       (SELECT count(*) FROM order_items oi WHERE oi.order_id = o.id) AS items
  FROM orders o WHERE conversation_id = '...';

-- after the customer confirms
--   state must be PENDING_CONFIRMATION, never CONFIRMED  (section 15)
SELECT o.state, e.from_state, e.to_state, e.actor
  FROM orders o JOIN order_events e ON e.order_id = o.id;""")

LBL("Watch for")
BUL([
    "A field given at turn 2 still present at turn 5 — the merge must not erase.",
    "Exactly one DRAFT order per conversation, not one per message.",
    "Total computed from the database price, including the delivery fee.",
])

LBL("Files")
P("<font face='Courier'>src/orders/persist.ts</font>, "
  "<font face='Courier'>src/orders/draft.ts</font>, "
  "<font face='Courier'>src/worker/pipeline.ts</font> (step 9)")

# ------------------------------------------------------------------ 1
TASK(1, "Measure reply latency",
     "One live sample came in at 12.4s against an 8s p95 gate — but that sample "
     "included a failed model call and two retries. Optimising against one "
     "worst case puts effort in the wrong layer.")

LBL("Technical work")
P("Everything needed is already recorded. Collect 50 real replies, then read the "
  "distribution rather than the mean — the mean hides the tail that the gate "
  "is actually about.")

CODE("""SELECT
  count(*)                                              AS calls,
  percentile_cont(0.50) WITHIN GROUP (ORDER BY latency_ms) AS p50,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95,
  max(latency_ms)                                       AS worst,
  avg(input_tokens)::int  AS in_tok,
  avg(output_tokens)::int AS out_tok,
  model
FROM ai_decisions
WHERE created_at > now() - interval '7 days'
GROUP BY model;""")

LBL("Decides")
P("If p50 is already under 5s, Task 2 is the whole of the latency work and Task 7 "
  "can be dropped. If p50 is 7s+, the model call itself is the problem and model "
  "choice has to be revisited with an eval set.")

story.append(PageBreak())

# ------------------------------------------------------------------ 2
TASK(2, "Two safe latency fixes",
     "Both are hours of work, carry no quality risk, and are measurable "
     "immediately. Do them before anything that trades quality for speed.")

LBL("2a — Parallelise retrieval")
P("<font face='Courier'>retrieveContext</font> makes <b>6 sequential database "
  "round trips</b>: products, FAQs, history, contact, recent failures, draft "
  "order. They are independent of one another.")

CODE("""// src/ai/retrieval.ts — before
const products = await db.query(...);   // each waits for the previous
const faqs     = await db.query(...);
const history  = await db.query(...);

// after
const [products, faqs, history, contact, failures, draft] =
  await Promise.all([ ... ]);""")

P("Expected saving 100–400ms depending on database latency. On a remote database "
  "it is worth considerably more.")

NOTE("One caveat: all six run inside the same withTenant transaction, which uses a "
     "single pooled connection. Promise.all on one client serialises anyway. "
     "Either issue them on separate scoped connections, or accept the smaller win "
     "of combining the cheap ones into a single query with CTEs.")

LBL("2b — Lower maxOutputTokens")
P("Currently 1024. Replies are one or two sentences — roughly 40–120 tokens. The "
  "model is not billed for unused capacity, but generation time scales with what "
  "it actually produces, and a high ceiling gives it room to ramble.")

CODE("""// src/ai/gemini-client.ts
maxOutputTokens: 1024,   ->   maxOutputTokens: 256,""")

P("256 leaves headroom for an order read-back, which is the longest reply the "
  "assistant ever writes. Verify against the longest real reply in "
  "<font face='Courier'>outbound_messages</font> before lowering further.")

LBL("Acceptance")
BUL([
    "p50 and p95 re-measured with the Task 1 query and recorded.",
    "No change in intent accuracy or reply quality on the same messages.",
])

story.append(PageBreak())

# ------------------------------------------------------------------ 3
TASK(3, "Variants and stock-accurate answers",
     "This is the highest-risk correctness gap in the system. There is no "
     "product_variants table, so “size 40 thiyenawada?” is answered from "
     "the product-level status and is confidently wrong whenever one size is out.")

NOTE("A wrong stock answer produces an order the seller cannot fulfil. That costs "
     "them a customer and costs us the trust the product is built on — which is "
     "why this comes before images.")

LBL("Schema — migration 0013")
CODE("""CREATE TABLE product_variants (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  product_id    uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  label         text NOT NULL,          -- 'Size 40', 'Blue', 'Blue / 40'
  sku           text,
  price         numeric(12,2),          -- NULL = inherit the product price
  stock_status  stock_status NOT NULL DEFAULT 'AVAILABLE',
  quantity      integer,                -- optional; status is what we answer with
  is_active     boolean NOT NULL DEFAULT true,
  UNIQUE (tenant_id, product_id, label)
);
-- RLS: same tenant_isolation policy as every other table.""")

LBL("Technical work")
BUL([
    "<b>Variants are optional.</b> A product with no variant rows answers exactly "
    "as it does today. A shop selling one-size items is never made to model them.",
    "<b>Reuse the Singlish matcher.</b> Run variant labels through "
    "<font face='Courier'>generateAliasKeys</font> so “size 40”, "
    "“40 size” and “size40” fold to one key. This inherits every "
    "future Singlish improvement instead of adding a second matcher.",
    "<b>Retrieval returns variants</b> with the product, and the prompt renders "
    "them with their own stock status.",
    "<b>Price still comes from the database</b> — variant price if set, otherwise "
    "the product's. The model never sees either.",
    "<b>CSV import learns variants.</b> A 'Size' or 'Variant' column becomes "
    "variant rows rather than five near-duplicate products.",
])

LBL("Answering rules — in code, not in the prompt")
TABLE(
    ["Situation", "Behaviour"],
    [
        ["No variants exist", "Answer from product stock_status (unchanged)"],
        ["Variant named, in stock", "Answer yes, with that variant's price"],
        ["Variant named, out of stock", "Say so; offer the sizes that ARE in stock"],
        ["Variant named, not in catalogue", "Hand off. Never guess"],
        ["No variant named, several exist", "Ask which, before quoting anything"],
        ["Any OUT_OF_STOCK variant", "Never enters a draft order"],
    ],
    [60 * mm, 106 * mm],
)

LBL("Acceptance")
BUL([
    "“size 40 thiyenawada?” answers from the variant row.",
    "An out-of-stock size is never sold, and the reply offers what is available.",
    "A shop with no variants sees no behaviour change at all.",
])

story.append(PageBreak())

# ------------------------------------------------------------------ 4
TASK(4, "Finish the order loop",
     "The order reaches PENDING_CONFIRMATION. What is missing is everything that "
     "makes the seller notice and act on it.")

LBL("4a — Today tiles")
P("The dashboard already counts orders. What it does not show is the number the "
  "seller has to act on.")

TABLE(
    ["Tile", "Query basis"],
    [
        ["Waiting for your confirmation", "state = 'PENDING_CONFIRMATION'"],
        ["Captured by the assistant today",
         "conversation_id IS NOT NULL AND created_at::date = current_date"],
        ["Drafts in progress", "state = 'DRAFT'"],
    ],
    [58 * mm, 108 * mm],
)

P("The third is worth building even though nobody asks for it: a rising count of "
  "abandoned drafts is the earliest signal that customers are giving up partway "
  "through the order flow, and it is invisible in every other metric.")

LBL("4b — Notification")
P("<font face='Courier'>notifySeller()</font> in "
  "<font face='Courier'>pipeline.ts</font> is still a stub. A confirmed order "
  "nobody is told about sits until the seller happens to look.")
BUL([
    "Minimum: unread badge already works — surface PENDING_CONFIRMATION count on "
    "the Orders tab the same way.",
    "Better: browser push via the PWA, which needs a service worker and "
    "VAPID keys.",
    "Do NOT send the seller a WhatsApp message per order — at 30 orders a day "
    "that is 30 notifications and they will mute the number.",
])

LBL("4c — Stock check at confirmation")
P("Nothing currently prevents an order for an item that went out of stock during "
  "the conversation. Re-check every line at the moment the customer confirms; if "
  "anything is unavailable, do not place the order — hand off to the seller with "
  "the reason. Depends on Task 3.")

LBL("4d — Delivery fee by city")
P("<font face='Courier'>delivery_rules</font> has both "
  "<font face='Courier'>colombo_rate</font> and "
  "<font face='Courier'>outstation_rate</font>; "
  "<font face='Courier'>defaultDeliveryFee()</font> always uses the Colombo one. "
  "Select on the captured city, and fall back to outstation when the city is "
  "unknown — undercharging delivery is the seller's money, not ours.")

story.append(PageBreak())

# ------------------------------------------------------------------ 5
TASK(5, "Per-conversation memory",
     "Each buyer's history must inform the next message. “Eka kiyada?” "
     "after three messages about a saree has to resolve to that saree.")

LBL("The gap")
P("<font face='Courier'>retrieval.ts</font> passes the last 10 raw messages and "
  "nothing else. A 30-message conversation loses its beginning entirely, and the "
  "model re-infers what “eka” means every turn — sometimes differently "
  "from the turn before, which reads to the customer as the shop forgetting.")

LBL("5a — Conversation memory table (migration 0014)")
CODE("""CREATE TABLE conversation_memory (
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  key             text NOT NULL,   -- 'last_product', 'delivery_city', ...
  value           text NOT NULL,
  product_id      uuid REFERENCES products(id) ON DELETE SET NULL,
  updated_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (conversation_id, key)
);""")

P("Written by <b>code</b>, not by the model: whichever product retrieval matched "
  "with the highest score becomes <font face='Courier'>last_product</font>. No "
  "extra model call, no extra cost.")

LBL("5b — State the referent explicitly")
CODE("""&lt;conversation_memory&gt;
  Currently discussing: Silk Saree (id 7c9e...)
  Customer asked about: price, delivery to Kadawatha
&lt;/conversation_memory&gt;""")

P("Telling the model what “eka” refers to is far more reliable than "
  "hoping it re-derives the same answer from prose each turn.")

LBL("5c — Rolling summary")
P("Above 20 turns, replace the oldest half with a one-paragraph summary from a "
  "single cheap model call, stored on the conversation and refreshed every 10 "
  "further turns. Cost is amortised — roughly one extra call per 10 messages.")

CODE("""ALTER TABLE conversations
  ADD COLUMN summary text,
  ADD COLUMN summary_through_message_id uuid,
  ADD COLUMN summarised_at timestamptz;""")

LBL("Acceptance")
BUL([
    "“Silk saree kiyada?” → “delivery kiyada?” → "
    "“mata eka one” drafts an order for the SAREE.",
    "A 40-message conversation still answers correctly about message 2.",
    "Tokens per call stop growing with conversation length.",
])

story.append(PageBreak())

# ------------------------------------------------------------------ 6
TASK(6, "Images in chat",
     "A customer sends a photo and asks “meka thiyenawada?”. Today the "
     "image is detected, then discarded.")

LBL("The gap")
P("<font face='Courier'>session.ts</font> records "
  "<font face='Courier'>mediaType</font> and sets "
  "<font face='Courier'>mediaUrl: null</font>. Nothing is downloaded and nothing "
  "is looked at; the message reaches the inbox as an unhandled item.")

LBL("6a — Download and store")
CODE("""// src/channels/waweb/media.ts
downloadMediaMessage(raw, 'buffer', {})
  -> media/{tenantId}/{messageId}.{ext}
  -> messages.media_url    = relative path
  -> messages.media_sha256 = hash   // customers resend the same photo""")

LBL("6b — Vision in the same call")
P("Gemini accepts images natively — a real advantage of the provider already "
  "chosen. Attach the image to the call that already classifies intent, so an "
  "image message costs one model call, not two.")

LBL("6c — Match through the existing matcher")
P("Ask the model to <b>describe</b> the item and pick from the candidate list. "
  "Never ask it to produce a product id from an image. Run the description "
  "through the same alias and trigram matcher used for text, so image matching "
  "inherits every Singlish improvement for free.")

NOTE("Cost: an image adds roughly 250–1,000 input tokens. Downscale to 512px on "
     "the long edge before sending — product identification does not need more, "
     "and it keeps the added cost near Rs 0.10 rather than Rs 0.40.")

LBL("Also required")
BUL([
    "Media is untrusted input exactly as text is. The injection posture does not "
    "relax because the content is a picture.",
    "Never serve media from a public path without an authorisation check — one "
    "tenant's customer photos must not be reachable by another.",
    "A retention policy belongs in this task, not later: delete media after N "
    "days, keep the message row. Storage otherwise grows without bound.",
])

LBL("Acceptance")
BUL([
    "A photo of a stocked product is answered by name, with price and stock from "
    "the database.",
    "A photo of something not stocked hands off rather than guessing.",
    "The image is visible in the seller inbox.",
])

story.append(PageBreak())

# ------------------------------------------------------------------ 7
TASK(7, "Rule-based fast path",
     "A greeting does not need a model call. Removing the model from the "
     "cheapest messages is the largest single latency and cost win available.")

LBL("Technical work")
P("A narrow exact-match table checked before the model call, in "
  "<font face='Courier'>pipeline.ts</font> after the spend guards:")

CODE("""hi · hello · hey · ayubowan · ayubowan!   -> greeting reply
sthuthi · thanks · thank you · bohoma sthuthi -> acknowledgement
ok · okay · hari                              -> no reply at all""")

P("Expected to remove the model from 15–25% of messages, saving the whole call "
  "(2–3s) and its cost on each.")

NOTE("Keep it deliberately narrow: exact matches on greetings and thanks only, "
     "never anything that could be a question. The moment the rule table starts "
     "answering product questions it has become a second, worse assistant that "
     "nobody is measuring.")

LBL("Why last")
P("It needs real intent data from Task 1 to be drawn safely. Guessing which "
  "messages are trivial, before seeing what customers actually send, is how a "
  "real question ends up answered with “Ayubowan!”.")

LBL("Acceptance")
BUL([
    "Greeting-only messages reply in under 500ms with no model call.",
    "No message containing a question mark, a product name or a number is ever "
    "matched by the fast path.",
    "<font face='Courier'>ai_decisions</font> shows the drop in call volume.",
])

# ------------------------------------------------------------------ gates
story.append(Paragraph("Release gates — unchanged", S["task"]))
story.append(Paragraph(
    "These do not move for any task above.", S["why"]))

TABLE(
    ["Gate", "Threshold", "Where measured"],
    [
        ["Price hallucinations", "Zero. One blocks release",
         "ai_decisions.gate_triggered"],
        ["Intent accuracy", "85%", "Needs a labelled set — see below"],
        ["Reply latency", "5s median, 8s p95", "ai_decisions.latency_ms"],
    ],
    [45 * mm, 48 * mm, 73 * mm],
)

P("<b>The labelled set does not exist yet, and building it is worth more than any "
  "single task above.</b> 100–200 real Sri Lankan customer messages with the "
  "correct intent and the correct reply attached. Without it, every change to the "
  "prompt or the model is an opinion; with it, each one becomes a measurement. It "
  "also supplies the 12–20 real few-shot examples the prompt still carries as "
  "placeholders.")

GAP(10)
story.append(Paragraph(
    "<i>Written against the codebase as it stands: 11 migrations, 43 source "
    "files, 13 test files. Every gap listed was verified in the code, not "
    "assumed.</i>", S["why"]))


def decorate(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 16 * mm, 190 * mm, 16 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(SOFT)
    canvas.drawString(20 * mm, 11 * mm, "Ordo — what to build next")
    canvas.drawRightString(190 * mm, 11 * mm, "Page %d" % doc.page)
    canvas.restoreState()


doc = BaseDocTemplate(
    "docs/Ordo-technical-plan.pdf", pagesize=A4,
    leftMargin=20 * mm, rightMargin=20 * mm,
    topMargin=18 * mm, bottomMargin=22 * mm,
    title="Ordo - What to build next", author="Ordo",
)
doc.addPageTemplates([PageTemplate(
    id="main",
    frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")],
    onPage=decorate)])
doc.build(story)
print("written: docs/Ordo-technical-plan.pdf")
