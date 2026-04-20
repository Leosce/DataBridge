import asyncio
import os
from dotenv import load_dotenv
from main import AIAgent

load_dotenv()

keys = {
    "groq": os.getenv("GROQ_API_KEY"),
    "nvidia": os.getenv("NVIDIA_API_KEY"),
    "gemini": os.getenv("GEMINI_API_KEY")
}

# --- Test Cases ---
TESTS = [
    # {
    #     "id": "T01",
    #     "category": "Schema Read",
    #     "input": "show me the columns in the marketing file",
    #     "expect_keywords": ["Campaign ID", "Channel", "Revenue Generated"],
    #     "expect_tool": "get_schema"
    # },
    # {
    #     "id": "T02",
    #     "category": "Schema Read",
    #     "input": "what columns does the properties file have?",
    #     "expect_keywords": ["Listing ID", "City", "List Price"],
    #     "expect_tool": "get_schema"
    # },
    # {
    #     "id": "T03",
    #     "category": "Query - Numeric Filter",
    #     "input": "show me marketing campaigns with revenue greater than 100000",
    #     "expect_keywords": ["Revenue Generated", "CMP-"],
    #     "expect_tool": "query_data"
    # },
    # {
    #     "id": "T04",
    #     "category": "Query - String Filter",
    #     "input": "show me all Facebook campaigns in marketing",
    #     "expect_keywords": ["Facebook", "CMP-"],
    #     "expect_tool": "query_data"
    # },
    # {
    #     "id": "T05",
    #     "category": "Query - Max Value",
    #     "input": "which marketing campaign generated the most revenue?",
    #     "expect_keywords": ["Revenue Generated", "CMP-"],
    #     "expect_tool": "query_data"
    # },
    # {
    #     "id": "T06",
    #     "category": "Query - Min Value",
    #     "input": "which property has the lowest list price?",
    #     "expect_keywords": ["List Price", "Listing ID"],
    #     "expect_tool": "query_data"
    # },
    # {
    #     "id": "T07",
    #     "category": "Query - Multi Condition",
    #     "input": "show me Email campaigns in marketing with more than 1000 conversions",
    #     "expect_keywords": ["Email", "Conversions"],
    #     "expect_tool": "query_data"
    # },
    {
        "id": "T08",
        "category": "Missing Values",
        "input": "are there any rows with missing values in marketing?",
        "expect_keywords": ["missing", "found", "row"],
        "expect_tool": "find_missing_rows"
    },
    # {
    #     "id": "T09",
    #     "category": "Row Index Lookup",
    #     "input": "what is the row index of campaign CMP-8001?",
    #     "expect_keywords": ["0", "index"],
    #     "expect_tool": "get_row_index"
    # },
    # {
    #     "id": "T10",
    #     "category": "Greeting - No Tool",
    #     "input": "hi",
    #     "expect_keywords": ["help", "assist", "hello", "hi"],
    #     "expect_tool": None
    # },
    # {
    #     "id": "T11",
    #     "category": "Insert Record",
    #     "input": "add a new marketing campaign called 'Test Campaign' on Facebook with a budget of 5000",
    #     "expect_keywords": ["__CONFIRM__", "add", "Test Campaign"],
    #     "expect_tool": "add_record"
    # },
    # {
    #     "id": "T12",
    #     "category": "Update Record",
    #     "input": "update the first marketing record to have revenue of 99999",
    #     "expect_keywords": ["__CONFIRM__", "Revenue Generated", "99999"],
    #     "expect_tool": "update_record"
    # },
    # {
    #     "id": "T13",
    #     "category": "Delete Record",
    #     "input": "delete the marketing campaign with the lowest revenue",
    #     "expect_keywords": ["__CONFIRM__", "delete", "Revenue Generated"],
    #     "expect_tool": "delete_record"
    # },
    # {
    #     "id": "T14",
    #     "category": "Properties Query",
    #     "input": "show me all properties in California with more than 3 bedrooms",
    #     "expect_keywords": ["CA", "Bedrooms"],
    #     "expect_tool": "query_data"
    # },
    # {
    #     "id": "T15",
    #     "category": "Properties Query",
    #     "input": "what is the most expensive property listed?",
    #     "expect_keywords": ["List Price", "Listing ID"],
    #     "expect_tool": "query_data"
    # },
    # {
    {
        "id": "T16",
        "category": "Multi-step Reasoning",
        "input": "which channel in marketing has the highest average revenue?",
        "expect_keywords": ["Channel", "Revenue Generated", "Mean"],
        "expect_tool": "summarize_data"
    },
    {
        "id": "T17",
        "category": "Multi-step Reasoning",
        "input": "compare the total budget vs total revenue for all marketing campaigns",
        "expect_keywords": ["Budget", "Revenue", "Total"],
        "expect_tool": "summarize_data"
    },
    # {
    #     "id": "T18",
    #     "category": "Cross File Awareness",
    #     "input": "how many records are in each file?",
    #     "expect_keywords": ["properties", "marketing"],
    #     "expect_tool": "get_schema"
    # },
    # {
    #     "id": "T19",
    #     "category": "Edge Case - Invalid Column",
    #     "input": "show me the profit column in marketing",
    #     "expect_keywords": ["not found", "Error", "available", "columns"],
    #     "expect_tool": "query_data"
    # },
    # {
    #     "id": "T20",
    #     "category": "Edge Case - Ambiguous",
    #     "input": "show me the best campaigns",
    #     "expect_keywords": ["Revenue", "CMP-"],  # should pick a sensible metric
    #     "expect_tool": "query_data"
    # },
]

# --- Runner ---
async def run_test(model_choice: str, test: dict) -> dict:
    agent = AIAgent(model_choice=model_choice, api_keys=keys)
    full_response = ""
    tools_called = []

    try:
        async for step in agent.chat(test["input"]):
            if step and not step.startswith("__CONFIRM__:"):
                full_response += step + "\n"
                # Detect which tools were called
                for tool in ["get_schema", "query_data", "get_row_index", 
                             "find_missing_rows", "delete_missing_rows",
                             "add_record", "update_record", "delete_record"]:
                    if f"{tool}(" in step and tool not in tools_called:
                        tools_called.append(tool)

        # Evaluate results
        keyword_hits = [kw for kw in test["expect_keywords"] 
                       if kw.lower() in full_response.lower()]
        keyword_pass = len(keyword_hits) == len(test["expect_keywords"])

        if test["expect_tool"] is None:
            tool_pass = len(tools_called) == 0
        else:
            tool_pass = test["expect_tool"] in tools_called

        passed = keyword_pass and tool_pass

        return {
            "id": test["id"],
            "category": test["category"],
            "input": test["input"],
            "passed": passed,
            "keyword_pass": keyword_pass,
            "tool_pass": tool_pass,
            "tools_called": tools_called,
            "missing_keywords": [kw for kw in test["expect_keywords"] 
                                 if kw.lower() not in full_response.lower()],
            "response_preview": full_response[:200].replace("\n", " ")
        }

    except Exception as e:
        return {
            "id": test["id"],
            "category": test["category"],
            "input": test["input"],
            "passed": False,
            "keyword_pass": False,
            "tool_pass": False,
            "tools_called": [],
            "missing_keywords": test["expect_keywords"],
            "response_preview": f"EXCEPTION: {str(e)}"
        }


async def run_model(model_choice: str):
    print(f"\n{'='*60}")
    print(f"  MODEL: {model_choice}")
    print(f"{'='*60}")

    results = []
    for test in TESTS:
        print(f"  Running {test['id']} - {test['category']}...", end=" ")
        result = await run_test(model_choice, test)
        results.append(result)
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(status)

    # Summary
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n  Score: {passed}/{total} ({round(passed/total*100)}%)")

    # Print failures
    failures = [r for r in results if not r["passed"]]
    if failures:
        print(f"\n  Failed Tests:")
        for f in failures:
            print(f"    [{f['id']}] {f['category']}")
            print(f"      Input:            {f['input']}")
            print(f"      Tools called:     {f['tools_called']}")
            print(f"      Missing keywords: {f['missing_keywords']}")
            print(f"      Tool check:       {'✅' if f['tool_pass'] else '❌'}")
            print(f"      Keyword check:    {'✅' if f['keyword_pass'] else '❌'}")
            print(f"      Response:         {f['response_preview']}")

    return {"model": model_choice, "passed": passed, "total": total, "results": results}


async def main():
    models = [
        "Groq (Llama 3.3)",
        "NVIDIA (Llama 3.3)",
        "Gemini (2.5 Flash)"
    ]

    all_results = []
    for model in models:
        result = await run_model(model)
        all_results.append(result)

    # Final comparison table
    print(f"\n{'='*60}")
    print("  FINAL COMPARISON")
    print(f"{'='*60}")
    print(f"  {'Model':<25} {'Score':<10} {'Pass Rate'}")
    print(f"  {'-'*45}")
    for r in all_results:
        rate = round(r['passed'] / r['total'] * 100)
        bar = "█" * (rate // 10) + "░" * (10 - rate // 10)
        print(f"  {r['model']:<25} {r['passed']}/{r['total']:<8} {bar} {rate}%")

    # Category breakdown
    print(f"\n  CATEGORY BREAKDOWN")
    print(f"  {'-'*45}")
    categories = list(set(t["category"] for t in TESTS))
    for cat in categories:
        cat_tests = [t["id"] for t in TESTS if t["category"] == cat]
        print(f"\n  {cat}:")
        for r in all_results:
            cat_results = [res for res in r["results"] if res["id"] in cat_tests]
            cat_passed = sum(1 for res in cat_results if res["passed"])
            print(f"    {r['model']:<25} {cat_passed}/{len(cat_results)}")


if __name__ == "__main__":
    asyncio.run(main())