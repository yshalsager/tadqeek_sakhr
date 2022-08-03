# tadqeek.alsharekh.org
import asyncio
from argparse import ArgumentParser
import json
from pathlib import Path

from httpx import AsyncClient, HTTPError

headers = {
    "authority": "cwg.sahehly.com",
    "accept": "application/json, text/plain, */*",
    "authorization": "Basic V2ViU2FoZWhseTo4dVc1c2FkN2dGRzJC",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
    "content-type": "application/json",
    "origin": "https://sahehly.com",
    "referer": "https://sahehly.com/",
}

url = "https://cwg.sahehly.com/Diac/Sahehly"

semaphore = asyncio.BoundedSemaphore(5)


async def fetch(url, data, headers, verbose=False):
    async with AsyncClient() as client:
        response = await client.post(url, data=data, headers=headers, timeout=300)
        try:
            response_json = response.json()
            if verbose:
                print(response_json["totalError"])
            return response_json["diacWord"]
        except HTTPError as err:
            raise RuntimeError(
                f"{err}\nUnable to process, got response:\n{response.text}\n."
            )


async def bound_fetch(sem, url, data, headers, verbose=False):
    # Getter function with semaphore.
    async with sem:
        return await fetch(url, data, headers, verbose=verbose)


# def chunkify_text(text, chunk_size=4900):
#     """
#     :param text: text to chunkify
#     :param chunk_size: size of each chunk
#     :return: list of chunks
#     """
#     return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def chunkify_text(text, chunk_size=4950):
    chunks = []
    for word in text.split(" "):
        if chunks and len(chunks[-1]) + len(word) > chunk_size:
            chunks.append("")
        if chunks:
            chunks[-1] += f"{word} "
        else:
            chunks.append(f"{word} ")
    return chunks


async def main(input_file: Path, output_file: Path, verbose=False):
    output_file_text = ""
    print("Splitting text into chunks...")
    chunks = chunkify_text(input_file.read_text(encoding="utf-8"))
    print(f"{len(chunks)} chunks found.")
    print("Starting spellcheck...")
    tasks = [
        asyncio.ensure_future(
            bound_fetch(
                semaphore,
                url,
                json.dumps({"type": "SWeb", "word": chunk, "gFlag": True}),
                headers,
                verbose=verbose,
            )
        )
        for chunk in chunks
    ]
    results = await asyncio.gather(*tasks)
    for result in results:
        if result:
            output_file_text += result
    output_file.write_text(output_file_text, encoding="utf-8")
    print("Done!")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        help="Path of text file to be checked.",
        required=True,
        type=Path,
    )
    parser.add_argument("-o", "--output", help="Path of output file.", type=Path)
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print API responses."
    )
    args = parser.parse_args()
    output_file = (
        args.output if args.output else Path(f"{args.input.stem}_{args.input.suffix}")
    )
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main(args.input, output_file, verbose=args.verbose))
    loop.run_until_complete(future)
