Ingest content into a company's knowledge base. Usage: /kb-ingest <source-type> <source>

Source types:
- `catalog`: CSV or JSON file with products/services
- `document`: PDF, TXT, or MD file with company info
- `instagram`: Instagram profile URL → scrape recent posts
- `website`: URL → scrape and extract content
- `faq`: JSON file with Q&A pairs
- `manual`: Interactive — ask user for title + content

Steps:
1. Parse source content based on type
2. Split into chunks if needed (max 1000 tokens per chunk)
3. Generate embeddings via embedding API
4. Store in knowledge_items table with proper metadata
5. Report: items ingested, tokens used, any errors
