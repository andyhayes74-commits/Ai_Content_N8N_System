# Request Analysis Prompt
Return strict JSON matching `schemas/request_analysis.schema.json`.
Rules: separate facts vs assumptions, never invent unsupported claims, flag missing info, and mark risky/legal/medical/financial claim-heavy areas.
Inputs: brief_text, asset_index, client_profile.
