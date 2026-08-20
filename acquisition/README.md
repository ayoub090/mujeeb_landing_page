# Mujeeb acquisition extractor

This optional service runs the MIT-licensed ScrapeGraphAI core on Mujeeb's own
infrastructure. It extracts public business facts from owner-supplied ecommerce
URLs. It does not log into websites, bypass access controls, or send messages.

Website content stays inside the deployment: ScrapeGraphAI talks to the local
Ollama service only. Start the `acquisition` Docker profile after setting
`ACQUISITION_ADMIN_KEY`. On the first controlled extraction, the service checks
for the configured model and downloads it once when absent.

The n8n workflow in `automation/n8n/mujeeb-acquisition-engine.json` calls this
service, posts normalized prospects to Mujeeb, and reports progress to Telegram.
