# Medical-device distributor discovery and qualification system

## Project at a glance

| | |
|---|---|
| Role | Requirements definition, workflow design, validation rules, and AI-assisted implementation |
| Operational context | Private distributor research and technical-commercial decision support |
| Public implementation | Python standard library, CSV/JSON, deterministic tests, synthetic data |
| Live-system interface | Google Sheets with staged review, approval gates, audit logs, and scheduled research cycles |
| Privacy boundary | Aggregate operating metrics only; no employer, product, market, company, or contact records |

## Objective

Distributor research becomes unreliable when search results, duplicate entities, incomplete evidence, and generic contact routes are mixed directly into an outreach list. I defined and iterated a human-in-the-loop system that separates discovery from approval:

1. Stage candidates from public evidence.
2. Normalize company identities and resolve duplicates.
3. Apply explicit distribution, sector, channel, manufacturer, and conflict gates.
4. Validate current decision-makers and person-specific public contact routes.
5. Hold uncertain records for review instead of silently promoting them.
6. Record changes, evidence quality, coverage gaps, and QA outcomes.

<img src="../../assets/distributor-qualification/workflow.svg" alt="Human-in-the-loop distributor qualification workflow" width="900">

## Private deployment evidence

The operational system is private. Only aggregate, dated evidence is reported here.

| Metric | Verified snapshot |
|---|---:|
| Distributor master records | 613 |
| Contact master records | 1,689 |
| Net growth from the imported baseline | +183 distributors; +259 contacts |
| Logged search-lane records | 70 |
| Candidate screenings represented in those logs | 2,186 |
| Unique company evaluations | 568 |
| Duplicate outcomes resolved or recorded | 1,097 |
| Rejected outcomes recorded | 110 |

The snapshot was verified on 23 August 2026. Search-lane totals are process counts and may include the same real-world identity appearing in different searches; that is why identity resolution is a core part of the system.

The latest recorded cycle screened 34 candidates, fully evaluated 23 unique companies, staged 13 companies and 25 contacts, and promoted 12 companies and 18 contacts after strict gates. It also recorded rejected, duplicate, and deferred outcomes and passed formula, orphan, and identity checks. This is a throughput statement—not a claim about hours saved.

## My contribution and AI use

I defined the operating objective, qualification and ranking logic, evidence standards, contactability rules, approval boundaries, and QA expectations. I then directed the iterative build and deployment using AI-assisted engineering and research tools.

The distinction matters: this project demonstrates process ownership, requirements engineering, technical validation, and responsible AI deployment. It does not claim that every research action or line of the private implementation was written manually.

## Public reconstruction

The code in this repository reconstructs the deterministic core on fictional records using reserved `.example` domains:

- [Qualification and QA pipeline](src/distributor_pipeline.py)
- [Synthetic company fixture](data/companies.synthetic.csv)
- [Synthetic contact fixture](data/contacts.synthetic.csv)
- [Unit and end-to-end tests](tests/test_distributor_pipeline.py)

The pipeline demonstrates:

- Company normalization across punctuation and common legal suffixes.
- Identity resolution using normalized names, root domains, and profile URLs.
- Deterministic Rank 1, Rank 2A, Rank 2B, Rank 3, and Rank 4 routing.
- Rejection of manufacturers, confirmed conflicts, and unsupported distributors.
- Review holds for incomplete or conflicting evidence.
- Contact deduplication and referential-integrity checks.
- Correct handling of `N/A`: placeholders never count as reachable routes or duplicate keys.
- Rejection of generic inboxes as person-specific contact routes.
- Human-controlled promotion requiring an approved company and at least one approved, qualified contact.
- CSV formula-injection protection and a machine-readable QA summary.

## Verified synthetic result

The included fixture produces:

| Stage | Result |
|---|---:|
| Company inputs | 10 |
| Unique companies after deduplication | 9 |
| Qualified / review / rejected | 3 / 3 / 3 |
| Contact inputs | 10 |
| Unique contacts after deduplication | 9 |
| Qualified / review | 4 / 5 |
| Promotion-ready companies | 2 |
| Automated QA checks | 7 passed |

## Run the reconstruction

From the repository root:

```bash
python projects/04-distributor-qualification/src/distributor_pipeline.py --companies projects/04-distributor-qualification/data/companies.synthetic.csv --contacts projects/04-distributor-qualification/data/contacts.synthetic.csv --output-dir build/distributor-demo
```

Run the tests:

```bash
python -m unittest discover -s projects/04-distributor-qualification/tests -v
```

## Boundaries and limitations

- The public code performs no web search, scraping, enrichment, messaging, or outreach.
- It is a compact portfolio reconstruction, not the private live implementation.
- The synthetic fixture does not measure search accuracy or market completeness.
- Aggregate deployment figures are dated snapshots, not continuously updated claims.
- No exact employer rules, product criteria, competitors, target markets, source URLs, spreadsheet links, or personal data are published.
- No quantified time-saving claim is made because a comparable manual baseline was not recorded.

[Back to portfolio](../../README.md)
