import os
import requests
import json
from crewai.tools import tool
from collections import Counter

@tool("Fetch and save US government contracts for a given company")
def fetch_contracts_by_company(company_name: str, output_folder: str = "output") -> str:
    """
    Fetches government contracts from USAspending API and writes summarized results to a text file.
    """
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

    payload = {
        "filters": {
            "recipient_search_text": [company_name],
            "award_type_codes": ["A", "B", "C", "D"]
        },
        "limit": 10,
        "page": 1,
        "fields": [
            "Award ID",
            "Recipient Name",
            "Start Date",
            "End Date",
            "Award Amount",
            "Awarding Agency",
            "Award Description"
        ],
        "sort": "Award Amount",
        "order": "desc"
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return f"❌ API Error: {response.status_code} - {response.text}"

        results = response.json().get("results", [])
        if not results:
            return f"No contracts found for '{company_name}'."

        # --- Build Summary ---
        total_award = 0
        agencies = set()
        years = set()
        description_words = []

        for item in results:
            total_award += item.get("Award Amount", 0) or 0

            agency = item.get("Awarding Agency", "").strip()
            if agency: agencies.add(agency)

            for date_field in ["Start Date", "End Date"]:
                date_str = item.get(date_field, "")
                if date_str and len(date_str) >= 4:
                    years.add(date_str[:4])

            desc = item.get("Award Description", "")
            if desc:
                description_words.extend(desc.lower().split())

        keyword_counts = Counter(description_words)
        common_terms = ", ".join(word for word, _ in keyword_counts.most_common(5))

        summary = (
            f"📄 Summary of Government Contracts for {company_name}\n"
            f"- Total Awarded: ${total_award:,.2f}\n"
            f"- Agencies Involved: {', '.join(sorted(agencies)) or 'N/A'}\n"
            f"- Years Active: {', '.join(sorted(years)) or 'N/A'}\n"
            f"- Common Keywords: {common_terms or 'N/A'}\n\n"
            + "=" * 80 + "\n\n"
        )

        # --- Save to File ---
        os.makedirs(output_folder, exist_ok=True)
        file_path = os.path.join(
            output_folder,
            f"{company_name.lower().replace(' ', '_')}_contracts.txt"
        )

        with open(file_path, "w") as f:
            f.write(summary)
            f.write("📋 Detailed Contract List:\n\n")
            for i, item in enumerate(results, 1):
                f.write(f"#{i}\n")
                f.write(f"Award ID: {item.get('Award ID', 'N/A')}\n")
                f.write(f"Recipient: {item.get('Recipient Name', 'N/A')}\n")
                f.write(f"Award Amount: ${item.get('Award Amount', 0):,.2f}\n")
                f.write(f"Start Date: {item.get('Start Date', 'N/A')}\n")
                f.write(f"End Date: {item.get('End Date', 'N/A')}\n")
                f.write(f"Agency: {item.get('Awarding Agency', 'N/A')}\n")
                f.write(f"Description: {item.get('Award Description', 'N/A')}\n")
                f.write("-" * 80 + "\n\n")

        return f"✅ Saved summarized contracts to '{file_path}'"

    except Exception as e:
        return f"❌ Request failed: {str(e)}"
