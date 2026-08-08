# MUJEEB Brand Book & Style Guide | مجيب

Welcome to the official Brand Guidelines for **Mujeeb | مجيب**, the premier Arabic AI order-confirmation SaaS for e-commerce stores in the Gulf Cooperation Council (GCC).

This document serves as the single source of truth for Mujeeb's visual identity, messaging architecture, and design components.

---

## 1. Brand Essence & Core Strategy

### 1.1 The Name & Identity
* **Name**: Mujeeb (English) | مجيب (Arabic).
* **Meaning**: "Responder" or "One who answers". It highlights speed, responsiveness, and service reliability.
* **Core Service**: Automating Cash on Delivery (COD) confirmations, address coordination, and customer routing using highly polite and culturally fluent AI over WhatsApp.

### 1.2 Core Brand Values
1. **Empirical Integrity**: We lead with measured data, not empty assumptions. We build trust by verifying success in real pilots.
2. **Cultural Fluency**: We speak the language of the merchant and customer natively, adapting perfectly to local GCC dialects.
3. **Respectful Boundaries**: Permission-aware contact. We do not engage in spam; we value the customer's preferred communication channel.
4. **Seamless Sovereignty**: We respect the merchant's choice of shipping carriers and telecom providers, adding value without disruption.

---

## 2. Color Systems

Mujeeb utilizes a dual color system to distinguish public marketing from operational dashboard environments.

### 2.1 Marketing & Public Brand (Trust & Technology)
Designed to emphasize authority, trust, and clean automation:
* **Deep Navy (`--color-blue-deep`)**: `#1E3A8A`
  * *Usage*: Primary brand text, heavy headings, dark buttons, trust elements.
* **Tech Blue (`--color-blue-primary`)**: `#2563EB`
  * *Usage*: Visual anchors, hyperlinks, primary marketing backgrounds.
* **Vibrant Emerald (`--color-green-primary`)**: `#059669`
  * *Usage*: High-priority calls to action, badges, confirmations.
* **Slate Gray (`--text-secondary`)**: `#475569`
  * *Usage*: Descriptive copy and secondary elements.

### 2.2 Product & Dashboard Brand (Organic Performance & Heritage)
Designed to feel calm, productive, and modern, echoing regional Gulf design sensibilities:
* **Forest Green (`--green`)**: `#116149`
  * *Usage*: Primary product text, active states, main brand accents.
* **Warm Mint (`--mint`)**: `#DCEEE7`
  * *Usage*: Light backgrounds for metrics, success indicators.
* **Desert Gold (`--gold` / `--sand`)**: `#E7AA51` / `#F3E9D6`
  * *Usage*: High-value metrics, pilot progression indicators, warm highlight backgrounds.
* **Charcoal Ink (`--ink`)**: `#17231F`
  * *Usage*: Primary interface body text.
* **RTO Crimson (`--red`)**: `#B74F4A`
  * *Usage*: Cancelled status labels, critical warning indicators.

---

## 3. Typography

Mujeeb uses highly readable, modern digital-native typography to accommodate bi-directional English and Arabic layouts.

### 3.1 Display & Headings (Arabic)
* **Primary Font**: `IBM Plex Sans Arabic` and `Alexandria`
* **Weights**: Bold (700), SemiBold (600), Medium (500)
* **Description**: Combining traditional Arabic calligraphic flow (Kufic characteristics) with geometric modern design. Used for all main site titles and navigation.

### 3.2 Display & Headings (English)
* **Primary Font**: `Inter`
* **Weights**: ExtraBold (800), Bold (700)
* **Description**: A modern neo-grotesque sans-serif built specifically for screen readability and numerical consistency.

### 3.3 UI Body Text & Numbers
* **Primary Font**: `IBM Plex Sans Arabic` (for text), `Inter` (for numbers and graphs)
* **Weights**: Regular (400), Light (300)
* **Aesthetic**: Numbers must always use `Inter` tabular figures for clean alignment in tables, billing sections, and KPI charts.

---

## 4. Logo Usage Guidelines

The Mujeeb logo exists as a typographic lockup combined with a distinct circular lettermark.

### 4.1 The Meem Lettermark
* The mark features the Arabic letter "م" (Meem) styled inside a circle (for Marketing) or a rounded square (for Product).
* The tail of the letter represents the continuous flow of information and clean, circular resolution.
* **Safe Space**: Always keep a padding equal to 25% of the logo's width around it.

### 4.2 Typographic Lockups
* **Primary Tech (LTR)**: `[Meem Circle Logo] Mujeeb | مجيب`
* **Primary Product (RTL)**: `مجيب | [Rounded Square Logo] Mujeeb`
* **Monochrome**: Use pure black/white assets on contrasting background shades. Do not use low-contrast grays for the logo.

---

## 5. Voice, Tone & Messaging Matrix

### 5.1 Messaging Core Rules
* **Be Specific**: Avoid vague terms like "boost conversion." Instead, write: "Reduce failed COD orders from 30% to 12%."
* **Stay Polite and Conversational**: On WhatsApp, represent the merchant faithfully. Say "السلام عليكم" (Peace be upon you) and use proper honorifics like "أخي الكريم" or "أختي الكريمة" if culturally aligned.
* **Respect Opt-out**: Always provide a simple exit command (e.g., reply with "إلغاء" or "إيقاف").

### 5.2 Copywriting Examples
| Category | Good Copy (Do) | Bad Copy (Don't) |
|---|---|---|
| **Outreach** | "هل يؤكد فريقكم طلبات الدفع عند الاستلام يدوياً؟ نقيس الأثر على 50 طلباً." | "نظامنا الذكي يضمن لك زيادة أرباحك بنسبة 200% بدون أي جهد!" |
| **WhatsApp confirmation** | "السلام عليكم من متجر [X]. طلبك رقم [123] بقيمة [Y] ريال جاهز للشحن. لتأكيد الطلب اضغط تأكيد." | "تم تسجيل طلبك! يجب تأكيد الاستلام فوراً بالضغط على الرابط التالي!" |
| **Status updates** | "تم تأكيد طلبك بنجاح، وقمنا بإرسال التفاصيل لشركة الشحن." | "تم التعديل." (Too brief, lacks context) |

---

## 6. UI Component Patterns

### 6.1 Status Badges
* **Confirmed (مؤكد)**: Mint green background (`#E1F2EA`) with Forest Green text (`#187056`).
* **Cancelled (ملغي)**: Soft red background (`#F8E8E7`) with Dark Red text (`#AD4B48`).
* **Human Follow-Up (متابعة يدوية)**: Warm amber background (`#FFF0D8`) with Brown-Amber text (`#9A6417`).

### 6.2 Buttons & Interaction
* **Marketing Primary Call-To-Action**: Emerald green with small box shadow.
* **Product Primary action**: Forest green background.
* **Accent highlights**: Desert gold border / badge tags.
