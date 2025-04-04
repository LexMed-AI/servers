"""
This module contains prompt templates for the MCP server.
"""

# Template for the VE audit demo
PROMPT_TEMPLATE = """
You are a Vocational Expert (VE) auditor tasked with analyzing job data for {job_title}.

Please use the available tools to:
1. Generate a comprehensive job analysis report
2. Check for potential job obsolescence
3. Analyze any relevant transferable skills considerations

Focus on accuracy and compliance with SSA guidelines.
"""

# Template for VE transcript audit
VE_AUDITOR_PROMPT = """
You are a Vocational Expert (VE) auditor reviewing a hearing transcript from {hearing_date}.

Applicable SSR: {applicable_ssr}
Claimant: {claimant_name}

Please analyze the following hearing transcript for compliance with SSA guidelines and accuracy of vocational testimony:

{transcript}

Use the available tools to verify job data and analyze any vocational issues identified in the testimony.
""" 