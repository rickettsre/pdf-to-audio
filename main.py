import PyPDF2
import os
import shutil
from dotenv import load_dotenv
from urllib.request import urlretrieve
from urllib.parse import urlencode
from pydub import AudioSegment


PDF = "./input/HSM_redp4126.pdf"
INPUT_DIRECTORY = "./input"
OUTPUT_DIRECTORY = "./output"
VOICERSS_END_POINT = "https://api.voicerss.org/?"

load_dotenv()


def clear_output_dir():
    if os.path.exists(OUTPUT_DIRECTORY):
        shutil.rmtree(OUTPUT_DIRECTORY)
    os.mkdir(OUTPUT_DIRECTORY)


def extract_pdf_text(pdf_to_convert: str):
    """This function uses PyPDF2 to extract text from all pages of a given pdf

    Args:
        pdf_to_convert (str): path to pdf file to

    Returns:
        pdf_content : The function will print a list of the total number of pages in the pdf then return a string of all of the extracted text.
    """
    pdf_content = ""
    with open(pdf_to_convert, "rb") as file:
        if file:
            read_pdf = PyPDF2.PdfReader(file)
            print(
                f"Total number of pages in {pdf_to_convert.split('/')[-1]} : {len(read_pdf.pages)}\n\n"
            )

            for page in read_pdf.pages:
                pdf_content += page.extract_text()
            return pdf_content


def pdf_to_voice(pdf_extract: list, batch_num: int):
    """This function will take the formated list of strings and it's batch number.

    Args:
        pdf_extract (list): _description_
        batch_num (int): batch number as we have to split the conversion into a number of mp3s due to FREE plan limit of https://www.voicerss.org/
    """

    filename = f"{OUTPUT_DIRECTORY}/speech_{batch_num}.mp3"
    src = ",".join(pdf_extract)

    PARAMETERS = {
        "key": os.environ.get("VOICERSS_API_KEY"),
        "src": src,
        "hl": "en-gb",
        "v": "Harry",
        "c": "MP3&f=16khz_16bit_stereo",
    }
    qstr = urlencode(PARAMETERS)

    try:
        urlretrieve(VOICERSS_END_POINT + qstr, filename)
    except:
        print(f"Issue with {src}")


# Yield successive n-sized
# NB https://www.voicerss.org/ Limited to 100KB requests so split list into chunks of 3 sentences
def divide_chunks(list: list, num_chunks: int):
    """This function will take a list and split it into separate list chunks. NB https://www.voicerss.org/ Limited to 100KB requests so split list into chunks e.g. of 3 sentences

    Args:
        list (list): pdf extracted text which contains each sentence
        num_chunks (int): Number of smaller lists

    Yields:
        list: this will return the list split into smaller chunks
    """
    for i in range(0, len(list), num_chunks):
        yield list[i : i + num_chunks]


def combine_mp3s():
    """This function will gather the list of mp3s in the OUTPUT folder
    and combine them to one mp3"""
    # List all mp3 files in the directory
    mp3_files = [file for file in os.listdir(OUTPUT_DIRECTORY) if file.endswith(".mp3")]

    # Sort the mp3 files by their filename
    mp3_files.sort(key=lambda x: int(x.split("speech_")[1].split(".")[0]))

    # Initialize an empty audio segment to store the concatenated audio
    combined = AudioSegment.empty()

    # Iterate through each mp3 file and concatenate them
    for mp3_file in mp3_files:
        audio = AudioSegment.from_file(os.path.join(OUTPUT_DIRECTORY, mp3_file))
        combined += audio

    # Export the combined audio to a single MP3 file
    combined.export(f"{OUTPUT_DIRECTORY}/combined.mp3", format="mp3", bitrate="128k")


def main():
    clear_output_dir()
    pdf_extract = extract_pdf_text(PDF)
    new_list = [
        item.replace("\r", "").replace("\n", "").replace("  ", "")
        for item in pdf_extract.split(". ")
    ]

    n = 3
    x = list(divide_chunks(new_list, n))
    batch_num = 1
    for xs in x:
        pdf_to_voice(xs, batch_num)
        batch_num += 1
    combine_mp3s()


if __name__ == "__main__":
    main()
