# tadqeek.alsharekh.org
from argparse import ArgumentParser
from pathlib import Path
import asyncio
from aiohttp import ClientSession

import encodings.idna

headers = {
    "authority": "cwg.alsharekh.org",
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
    "content-type": "application/json",
    "origin": "https://tadqeek.alsharekh.org",
    "referer": "https://tadqeek.alsharekh.org/",
    "accept-language": "en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7",
}

url = "https://cwg.alsharekh.org/Diac/MarkWrongWords"


async def fetch(url, data, headers):
    async with ClientSession() as session:
        async with session.post(
            url, data=data.encode("utf-8"), headers=headers
        ) as response:
            response_json = await response.json()
            return response_json["diacWord"]


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


async def main(input_file: Path, output_file: Path):
    output_file_text = ""
    print("Splitting text into chunks...")
    chunks = chunkify_text(input_file.read_text())
    print(f"{len(chunks)} chunks found.")
    print("Starting spellcheck...")
    tasks = [
        asyncio.ensure_future(
            fetch(url, '{"word": "' + chunk + '", "type": 0}', headers)
        )
        for chunk in chunks
    ]
    results = await asyncio.gather(*tasks)
    for result in results:
        
        if result:
            output_file_text += result
    output_file.write_text(output_file_text)
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
    args = parser.parse_args()
    output_file = (
        args.output if args.output else Path(f"{args.input.stem}_{args.input.suffix}")
    )
    asyncio.run(main(args.input, output_file))
