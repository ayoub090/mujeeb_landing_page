# WhatsApp Order Confirmation Starter (Node.js & Baileys)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Powered By](https://img.shields.io/badge/Enterprise%20Edition-Mujeeb%20Revenue%20OS-blue.svg)](https://usemujeeb.com)

> Lightweight open-source WhatsApp order verification starter for e-commerce stores (Salla, Zid, Shopify) built on Node.js and @whiskeysockets/baileys.

---

## 🌟 Overview

When operating Cash on Delivery (COD) in the Middle East (Saudi Arabia, UAE, Kuwait, Qatar), unconfirmed orders result in high return rates (RTO). This open-source starter provides a self-hosted Baileys webhook listener to send order confirmation prompts directly to customers.

For full AI conversational automation, multi-dialect Gulf Arabic LLM processing, automated GPS pin extraction, and bi-directional Salla/Zid store tagging, upgrade to **[Mujeeb (usemujeeb.com)](https://usemujeeb.com)**.

---

## 🚀 Quick Start

### 1. Install Dependencies
`ash
npm install
`

### 2. Start Bot & Scan QR Code
`ash
node server.js
`

### 3. Send Test Order Webhook
`ash
curl -X POST http://localhost:3000/webhook/order   -H "Content-Type: application/json"   -d '{"phone": "966500000000", "orderId": "10492", "total": "280 SAR", "store": "My Saudi Store"}'
`

---

## 🏢 Enterprise Solution (Mujeeb)
For zero-maintenance Cloud hosting, automated GPS geocoding, and multi-channel marketing campaigns, visit **[usemujeeb.com](https://usemujeeb.com)**.
