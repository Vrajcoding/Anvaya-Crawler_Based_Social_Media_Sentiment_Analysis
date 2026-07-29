"""
test_x_crawler.py — Quick standalone test for the Selenium X crawler.
Run from the backend directory:
    python test_x_crawler.py "your search query here"

To open a visible browser window (needed if X blocks or requires verification):
    set X_HEADLESS=false && python test_x_crawler.py "protest india"
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from crawlers.selenium_x_crawler import selenium_x_search, _X_USERNAME, _X_PASSWORD, _X_HEADLESS


async def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "india protest"

    print("=" * 60)
    print("  X (Twitter) Selenium Crawler — Test Run")
    print("=" * 60)
    print(f"  Query    : {query!r}")
    print(f"  Username : {_X_USERNAME or '⚠️  NOT SET'}")
    print(f"  Password : {'*' * len(_X_PASSWORD) if _X_PASSWORD else '⚠️  NOT SET'}")
    print(f"  Headless : {_X_HEADLESS}")
    print("=" * 60)

    if not _X_USERNAME or not _X_PASSWORD:
        print("\n❌  X_USERNAME or X_PASSWORD is not set in .env — aborting.")
        return

    print("\n🚀 Starting Selenium X crawl (this may take 30-60 seconds)...\n")

    results = await selenium_x_search(query=query, limit=10)

    print("\n" + "=" * 60)
    if not results:
        print("❌  No results returned.")
        print("   Possible causes:")
        print("   • Login failed — check X credentials in .env")
        print("   • X blocked the account ('temporarily limited')")
        print("   • Try: set X_HEADLESS=false && python test_x_crawler.py")
    else:
        print(f"✅  Got {len(results)} real tweets!\n")
        for i, r in enumerate(results, 1):
            print(f"  [{i}] {r.author_username}")
            print(f"      {r.content[:120]}{'...' if len(r.content) > 120 else ''}")
            print(f"      ❤️  {r.engagement.likes}  🔁 {r.engagement.shares}  💬 {r.engagement.comments}")
            print(f"      🔗 {r.url}")
            print(f"      📋 source: {r.source_type}  |  {r.created_at[:19] if r.created_at else 'N/A'}")
            print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
