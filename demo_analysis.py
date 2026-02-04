#!/usr/bin/env python3
"""
Demo Script: Test Policy Analysis API

This script demonstrates how to:
1. Upload a policy PDF directly for analysis
2. Poll for completion status
3. Download the generated report

Usage:
    python demo_analysis.py /path/to/policy.pdf "Client Name" "Industry"

Example:
    python demo_analysis.py ./sample_policy.pdf "Acme Corp" "MSP/Technology Services"
"""

import sys
import time
import argparse
import requests


def main():
    parser = argparse.ArgumentParser(description="Test the Policy Analysis API")
    parser.add_argument("pdf_path", help="Path to the policy PDF file")
    parser.add_argument("client_name", help="Client company name")
    parser.add_argument(
        "industry",
        nargs="?",
        default="Other/General",
        help="Client industry (default: Other/General)"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Max seconds to wait for analysis (default: 300)"
    )

    args = parser.parse_args()

    api_url = args.api_url.rstrip("/")

    print("=" * 60)
    print("Rhône Risk Policy Analysis - Demo")
    print("=" * 60)
    print(f"API URL: {api_url}")
    print(f"Policy: {args.pdf_path}")
    print(f"Client: {args.client_name}")
    print(f"Industry: {args.industry}")
    print()

    # Step 1: Check API health
    print("1. Checking API health...")
    try:
        health = requests.get(f"{api_url}/health", timeout=5)
        health.raise_for_status()
        health_data = health.json()

        if not health_data.get("anthropic_configured"):
            print("   ⚠️  WARNING: Anthropic API key not configured!")
            print("   The analysis will fail without a valid API key.")
            response = input("   Continue anyway? (y/n): ")
            if response.lower() != "y":
                sys.exit(1)
        else:
            print("   ✓ API is healthy and configured")
    except Exception as e:
        print(f"   ✗ API health check failed: {e}")
        sys.exit(1)

    print()

    # Step 2: Upload policy
    print("2. Uploading policy for analysis...")
    try:
        with open(args.pdf_path, "rb") as f:
            files = {"file": (args.pdf_path.split("/")[-1], f, "application/pdf")}
            data = {
                "client_name": args.client_name,
                "client_industry": args.industry,
                "policy_type": "cyber",
                "renewal": "false",
            }

            response = requests.post(
                f"{api_url}/analysis/upload",
                files=files,
                data=data,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

        analysis_id = result["analysis_id"]
        print(f"   ✓ Upload successful!")
        print(f"   Analysis ID: {analysis_id}")
    except FileNotFoundError:
        print(f"   ✗ File not found: {args.pdf_path}")
        sys.exit(1)
    except Exception as e:
        print(f"   ✗ Upload failed: {e}")
        sys.exit(1)

    print()

    # Step 3: Poll for completion
    print("3. Waiting for analysis to complete...")
    start_time = time.time()
    last_progress = ""

    while True:
        elapsed = time.time() - start_time
        if elapsed > args.timeout:
            print(f"   ✗ Timeout after {args.timeout} seconds")
            sys.exit(1)

        try:
            status_response = requests.get(
                f"{api_url}/analysis/{analysis_id}/status",
                timeout=10,
            )
            status_response.raise_for_status()
            status = status_response.json()

            current_status = status.get("status", "unknown")
            progress = status.get("progress", "")

            if progress != last_progress:
                print(f"   [{int(elapsed)}s] {progress}")
                last_progress = progress

            if current_status == "completed":
                print(f"   ✓ Analysis completed in {int(elapsed)} seconds!")
                break
            elif current_status == "failed":
                print(f"   ✗ Analysis failed: {status.get('error', 'Unknown error')}")
                sys.exit(1)

            time.sleep(3)  # Poll every 3 seconds

        except Exception as e:
            print(f"   ⚠️  Status check error: {e}")
            time.sleep(5)

    print()

    # Step 4: Display results
    print("4. Analysis Results")
    print("-" * 40)

    result = status.get("result", {})
    analysis_data = result.get("analysis_data", {})
    exec_summary = analysis_data.get("executive_summary", {})
    key_metrics = exec_summary.get("key_metrics", {})

    print(f"   Overall Score: {key_metrics.get('overall_maturity_score', 'N/A')}/10")
    print(f"   Recommendation: {exec_summary.get('recommendation', 'N/A')}")
    print()

    # Strengths
    policy_summary = analysis_data.get("policy_summary", {})
    strengths = policy_summary.get("strengths", [])
    if strengths:
        print("   Key Strengths:")
        for s in strengths[:3]:
            print(f"     • {s}")
        print()

    # Deficiencies
    deficiencies = policy_summary.get("critical_deficiencies", [])
    if deficiencies:
        print("   Critical Deficiencies:")
        for d in deficiencies[:3]:
            print(f"     ⚠️  {d}")
        print()

    # Report path
    report_path = result.get("report_path")
    if report_path:
        print(f"   📄 Report generated: {report_path}")
        print(f"   Download: GET {api_url}/analysis/{analysis_id}/report")

    print()
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
