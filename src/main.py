import asyncio
import sys

from coordinator import coordinator


async def main():
    topic = sys.argv[1]

    result = await coordinator.research(topic)

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
