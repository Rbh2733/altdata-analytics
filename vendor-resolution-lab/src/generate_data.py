"""Deterministic synthetic vendor-spend generator.

Builds the three inputs the lab runs on, seeded so every run is identical:
  data/canonical_vendors.csv   the vendor master (name, category, aliases)
  data/transactions.csv        raw merchant strings the way card and invoice
                               feeds actually deliver them
  data/labels.csv              ground truth (raw_id -> true vendor), used only
                               for evaluation, never by the pipeline

The mess is deliberate and labeled. Processor prefixes, store numbers,
truncation to card-network field widths, typos, and a two-part week-7 drift
event are all seeded here so the pipeline's failure modes are reproducible.
The drift has two independent components, the way real feed breaks do:
a new processor format (PYUSD-, unknown to the normalizer on purpose) that
hits a quarter of ALL weeks 7-8 rows, and six vendors deliberately missing
from the master.
"""

import csv
import random
from pathlib import Path

SEED = 7
WEEKS = 8
ROWS_PER_WEEK = 7500
DATA = Path(__file__).resolve().parent.parent / "data"

# (name, category, extra aliases beyond the generated ones)
VENDORS = [
    ("OpenAI", "AI and ML Platforms", ["OPENAI CHATGPT SUBSCR", "OPENAI API"]),
    ("Anthropic", "AI and ML Platforms", ["ANTHROPIC CLAUDE.AI", "CLAUDE AI SUBSCR"]),
    ("Cohere", "AI and ML Platforms", ["COHERE TECH"]),
    ("Mistral AI", "AI and ML Platforms", ["MISTRAL"]),
    ("Hugging Face", "AI and ML Platforms", ["HUGGINGFACE HUB", "HF SPACES"]),
    ("Perplexity", "AI and ML Platforms", ["PERPLEXITY.AI SUBSCR"]),
    ("Midjourney", "AI and ML Platforms", ["MIDJOURNEY INC"]),
    ("ElevenLabs", "AI and ML Platforms", ["ELEVEN LABS IO"]),
    ("Runway ML", "AI and ML Platforms", ["RUNWAYML"]),
    ("Scale AI", "AI and ML Platforms", ["SCALE LABS"]),
    ("Amazon Web Services", "Cloud Infrastructure", ["AWS", "AWS EMEA", "AMAZON WEB SERV"]),
    ("Microsoft Azure", "Cloud Infrastructure", ["MSFT AZURE", "AZURE CLOUD"]),
    ("Google Cloud", "Cloud Infrastructure", ["GCP", "GOOGLE CLOUD EMEA"]),
    ("DigitalOcean", "Cloud Infrastructure", ["DIGITAL OCEAN"]),
    ("Cloudflare", "Cloud Infrastructure", ["CLOUDFLARE NET"]),
    ("Fastly", "Cloud Infrastructure", []),
    ("Linode", "Cloud Infrastructure", ["AKAMAI LINODE"]),
    ("Vercel", "Cloud Infrastructure", ["VERCEL HOSTING"]),
    ("Netlify", "Cloud Infrastructure", []),
    ("Hetzner", "Cloud Infrastructure", ["HETZNER ONLINE"]),
    ("OVHcloud", "Cloud Infrastructure", ["OVH"]),
    ("Heroku", "Cloud Infrastructure", ["HEROKU DYNOS"]),
    ("GitHub", "Developer Tools", ["GITHUB COPILOT", "GH ACTIONS"]),
    ("GitLab", "Developer Tools", []),
    ("JetBrains", "Developer Tools", ["JETBRAINS AMER", "INTELLIJ LIC"]),
    ("Docker", "Developer Tools", ["DOCKER HUB"]),
    ("HashiCorp", "Developer Tools", ["HASHICORP CLOUD"]),
    ("Postman", "Developer Tools", []),
    ("CircleCI", "Developer Tools", ["CIRCLE INTERNET SVC"]),
    ("Sentry", "Developer Tools", ["SENTRY.IO", "FUNCTIONAL SOFTWARE"]),
    ("New Relic", "Developer Tools", ["NEWRELIC"]),
    ("Datadog", "Developer Tools", ["DATADOG CLOUD MON"]),
    ("PagerDuty", "Developer Tools", []),
    ("LaunchDarkly", "Developer Tools", []),
    ("Snowflake", "Data Infrastructure", ["SNOWFLAKE COMPUTING"]),
    ("Databricks", "Data Infrastructure", ["DATABRICKS INC"]),
    ("MongoDB", "Data Infrastructure", ["MONGODB ATLAS", "MONGODB CLOUD"]),
    ("Confluent", "Data Infrastructure", ["CONFLUENT KAFKA"]),
    ("Elastic", "Data Infrastructure", ["ELASTIC CLOUD", "ELASTICSEARCH"]),
    ("Redis", "Data Infrastructure", ["REDIS LABS"]),
    ("PlanetScale", "Data Infrastructure", []),
    ("Supabase", "Data Infrastructure", []),
    ("Fivetran", "Data Infrastructure", []),
    ("dbt Labs", "Data Infrastructure", ["DBT CLOUD"]),
    ("Airbyte", "Data Infrastructure", []),
    ("Segment", "Data Infrastructure", ["TWILIO SEGMENT"]),
    ("Slack", "SaaS Productivity", ["SLACK TECHNOLOGIES"]),
    ("Notion", "SaaS Productivity", ["NOTION LABS"]),
    ("Zoom", "SaaS Productivity", ["ZOOM.US", "ZOOM VIDEO COMM"]),
    ("Atlassian", "SaaS Productivity", ["ATLASSIAN JIRA", "ATLASSIAN CONFLUENCE"]),
    ("Asana", "SaaS Productivity", []),
    ("Monday.com", "SaaS Productivity", ["MONDAY COM LTD"]),
    ("Airtable", "SaaS Productivity", []),
    ("Figma", "SaaS Productivity", ["FIGMA MONTHLY RENEW"]),
    ("Canva", "SaaS Productivity", ["CANVA PTY"]),
    ("Miro", "SaaS Productivity", ["REALTIMEBOARD"]),
    ("Calendly", "SaaS Productivity", []),
    ("Loom", "SaaS Productivity", []),
    ("Dropbox", "SaaS Productivity", ["DROPBOX INTL"]),
    ("Box", "SaaS Productivity", ["BOX.COM"]),
    ("DocuSign", "SaaS Productivity", []),
    ("Grammarly", "SaaS Productivity", []),
    ("1Password", "Security", ["AGILEBITS"]),
    ("Okta", "Security", ["OKTA INC"]),
    ("CrowdStrike", "Security", ["CROWDSTRIKE FALCON"]),
    ("Cloudflare Zero Trust", "Security", ["CF ZERO TRUST"]),
    ("Snyk", "Security", []),
    ("Auth0", "Security", ["AUTH0 BY OKTA"]),
    ("NordLayer", "Security", ["NORD SECURITY"]),
    ("Stripe", "Payments and Fintech", ["STRIPE PAYMENTS"]),
    ("Plaid", "Payments and Fintech", ["PLAID TECHNOLOGIES"]),
    ("Brex", "Payments and Fintech", []),
    ("Ramp", "Payments and Fintech", ["RAMP BUSINESS CORP"]),
    ("Bill.com", "Payments and Fintech", ["BILL COM"]),
    ("Expensify", "Payments and Fintech", []),
    ("Salesforce", "Sales and Marketing", ["SFDC", "SALESFORCE.COM"]),
    ("HubSpot", "Sales and Marketing", []),
    ("Mailchimp", "Sales and Marketing", ["INTUIT MAILCHIMP"]),
    ("Twilio", "Sales and Marketing", ["TWILIO SMS"]),
    ("SendGrid", "Sales and Marketing", ["TWILIO SENDGRID"]),
    ("Intercom", "Sales and Marketing", []),
    ("Zendesk", "Sales and Marketing", []),
    ("Klaviyo", "Sales and Marketing", []),
    ("Semrush", "Sales and Marketing", []),
    ("Zapier", "Automation", []),
    ("Make.com", "Automation", ["MAKE INTEGROMAT"]),
    ("Retool", "Automation", []),
    ("Workato", "Automation", []),
]

# Week-7 drift: real-world pattern of a coverage gap. These vendors are absent
# from the canonical table on purpose, so the honest pipeline behavior is to
# flag them as new-vendor candidates rather than force a match.
NOVEL_VENDORS = [
    ("Fluxgrid AI", "AI and ML Platforms"),
    ("Tessellate Cloud", "Cloud Infrastructure"),
    ("Quorum Data", "Data Infrastructure"),
    ("Halcyon Compute", "Cloud Infrastructure"),
    ("Vector Foundry", "AI and ML Platforms"),
    ("Marginalia Systems", "Developer Tools"),
]

PREFIXES = ["", "", "", "", "SQ *", "PAYPAL *", "PP*", "STRIPE*", "FS *", "IN *", "WEB*"]
SUFFIXES = ["", "", "", " 0423", " #4821", " STORE 112", " NYC", " AUSTIN TX",
            " 800-555-0147", " .COM", " INC", " LLC", " RENEWAL", " MONTHLY"]
DRIFT_PREFIX = "PYUSD-"  # week-7 processor format change


def make_aliases(name: str, extras: list[str]) -> list[str]:
    up = name.upper()
    aliases = {up, up.replace(" ", ""), up.replace(".", "").replace(",", "")}
    aliases.update(a.upper() for a in extras)
    return sorted(aliases)


def decorate(rng: random.Random, alias: str, drift_format: bool) -> str:
    prefix = DRIFT_PREFIX if drift_format else rng.choice(PREFIXES)
    s = prefix + alias + rng.choice(SUFFIXES)
    if rng.random() < 0.30:
        s = s[: rng.randrange(18, 27)]  # card-network descriptor widths vary
    if rng.random() < 0.08 and len(s) > 6:
        i = rng.randrange(1, len(s) - 2)
        s = s[:i] + s[i + 1] + s[i] + s[i + 2:]  # adjacent-char typo
    if rng.random() < 0.10:
        s = s.replace(" ", "", 1)  # glued tokens, a common processor artifact
    if rng.random() < 0.05:
        s = s.replace(" ", "  ", 1)
    return s.upper()


def main() -> None:
    rng = random.Random(SEED)
    DATA.mkdir(exist_ok=True)

    vendor_rows = []
    alias_map = {}
    for name, category, extras in VENDORS:
        aliases = make_aliases(name, extras)
        vendor_rows.append({"vendor": name, "category": category, "aliases": "|".join(aliases)})
        alias_map[name] = aliases
    with open(DATA / "canonical_vendors.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["vendor", "category", "aliases"])
        w.writeheader()
        w.writerows(vendor_rows)

    # Zipf-ish popularity so spend concentrates the way real vendor books do
    weights = [1.0 / (i + 1) ** 0.7 for i in range(len(VENDORS))]

    tx_rows, label_rows = [], []
    raw_id = 0
    for week in range(1, WEEKS + 1):
        for _ in range(ROWS_PER_WEEK):
            raw_id += 1
            novel_row = week >= 7 and rng.random() < 0.08
            drift_format = week >= 7 and rng.random() < 0.25
            if novel_row:
                name, category = NOVEL_VENDORS[rng.randrange(len(NOVEL_VENDORS))]
                alias = name.upper() if rng.random() < 0.7 else name.upper().replace(" ", "")
            else:
                name, category, _ = rng.choices(VENDORS, weights=weights, k=1)[0]
                alias = rng.choice(alias_map[name])
            raw = decorate(rng, alias, drift_format)
            amount = round(rng.lognormvariate(4.2, 1.1), 2)
            tx_rows.append({"raw_id": raw_id, "week": week, "raw_string": raw, "amount": amount})
            label_rows.append({"raw_id": raw_id, "true_vendor": name,
                               "true_category": category,
                               "in_canonical": int(not novel_row)})

    with open(DATA / "transactions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["raw_id", "week", "raw_string", "amount"])
        w.writeheader()
        w.writerows(tx_rows)
    with open(DATA / "labels.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["raw_id", "true_vendor", "true_category", "in_canonical"])
        w.writeheader()
        w.writerows(label_rows)

    novel = sum(1 for r in label_rows if not r["in_canonical"])
    print(f"generated {len(tx_rows)} transactions across {WEEKS} weeks, "
          f"{len(VENDORS)} canonical vendors, {novel} rows from novel vendors (weeks 7-8)")


if __name__ == "__main__":
    main()
