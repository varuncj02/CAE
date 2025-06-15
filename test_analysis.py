#!/usr/bin/env python3
"""
Example script to test the conversation analysis API
"""

import asyncio
import httpx
import json
from uuid import UUID

# API base URL
BASE_URL = "http://localhost:8000"


async def test_conversation_analysis():
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(630.0)
    ) as client:  # 10.5 minutes timeout
        # First, create a user
        print("1. Creating a user...")
        user_response = await client.post(
            f"{BASE_URL}/users/", json={"name": "Test User"}
        )
        user = user_response.json()
        user_id = user["id"]
        print(f"   Created user: {user_id}")

        # Create a chat session and send a message
        print("\n2. Starting a conversation...")
        chat_response = await client.post(
            f"{BASE_URL}/chats/",
            json={
                "user_id": user_id,
                "message": "I'm feeling really overwhelmed with work lately. There's so much to do and I don't know where to start. I feel like I'm drowning.",
                "chat_id": None,
            },
        )
        messages = chat_response.json()
        chat_id = messages[0]["chat_id"]
        print(f"   Chat ID: {chat_id}")
        print(f"   User: {messages[0]['content']}")
        print(f"   Assistant: {messages[1]['content']}")

        # Add another exchange
        print("\n3. Continuing conversation...")
        chat_response2 = await client.post(
            f"{BASE_URL}/chats/",
            json={
                "user_id": user_id,
                "message": "I've tried making lists but I just feel paralyzed. Everything seems equally urgent and important.",
                "chat_id": chat_id,
            },
        )
        messages2 = chat_response2.json()
        print(f"   User: {messages2[-2]['content']}")
        print(f"   Assistant: {messages2[-1]['content']}")

        # Now analyze the conversation
        print("\n4. Analyzing conversation for best emotional response...")
        print(
            "   This may take several minutes as it simulates multiple conversation paths..."
        )

        start_time = asyncio.get_event_loop().time()

        analysis_response = await client.post(
            f"{BASE_URL}/analysis/",
            json={"chat_id": chat_id, "num_branches": 5, "simulation_depth": 3},
        )

        if analysis_response.status_code == 200:
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"   Analysis completed in {elapsed:.1f} seconds")

            analysis = analysis_response.json()

            print(f"\n   Analysis ID: {analysis['id']}")
            print(f"\n   === BRANCHES EXPLORED ===")

            for i, branch in enumerate(analysis["branches"]):
                print(f"\n   Branch {i + 1} (Score: {branch['eq_score']:.2f}):")
                print(f"   Response: {branch['response'][:100]}...")
                print(
                    f"   Key strengths: {', '.join(k for k, v in branch['scoring_breakdown'].items() if v > 0.8)}"
                )

            print(f"\n   === SELECTED RESPONSE ===")
            print(f"   Branch {analysis['selected_branch_index'] + 1} was selected")
            print(f"   Response: {analysis['selected_response']}")

            print(f"\n   === ANALYSIS ===")
            print(f"   {analysis['analysis']}")

            print(f"\n   === OVERALL SCORES ===")
            for metric, score in analysis["overall_scores"].items():
                print(f"   {metric}: {score:.2f}")
        else:
            print(f"   Error {analysis_response.status_code}: {analysis_response.text}")
            if analysis_response.status_code == 504:
                print(
                    "   The analysis timed out. Try reducing simulation_depth or num_branches."
                )

        # Get all analyses for this chat
        print("\n5. Retrieving all analyses for this chat...")
        all_analyses = await client.get(f"{BASE_URL}/analysis/{chat_id}")
        print(f"   Total analyses performed: {len(all_analyses.json())}")


if __name__ == "__main__":
    print("Conversation Analysis Engine Test")
    print("=================================")
    asyncio.run(test_conversation_analysis())
