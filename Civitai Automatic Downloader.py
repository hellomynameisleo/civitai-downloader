import requests
import os
import time
import re
import concurrent.futures
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup

api_key = "insert api key here"
api_url = "https://civitai.com/api/v1/models"
log_parsed_downloads_URL_path = Path(r"Path\Civitai\#log_parsed.txt") # Logs the model name already parsed
log_parsed_downloads_URL_images_path = Path(r"Path\Civitai\#log_parsed_images.txt") # Logs the model name already parsed
download_directory = r"Path\Civitai" # Define the download directory
max_parallel_tasks = 1 # How many items to parse in parallel

# page limit
while True:
    set_limit = input("Enter limit from 1-100 for scraping newest gallery models: ")
    if set_limit.isdigit():
        set_limit = int(set_limit)
        if 1 <= set_limit <= 100:
            break
        else:
            print("Invalid input. Please enter a number between 1 and 100.")
    else:
        print("Invalid input. Please enter a valid integer.")

# page number to parse
while True:
    page_range = input("Enter the page range (e.g., 1-5) or single page number for scraping newest gallery models: ")
    try:
        # page single number
        if page_range.isdigit():
            start = int(page_range)
            end = int(page_range)
            break
        else: 
            # page range number
            start, end = map(int, page_range.split("-"))
            if start != 0:
                if start <= end:
                    break
                else:
                    print("Invalid input range. Start number must be smaller than end number.")
            else:
                print(f"{start} is not a valid option")
    except ValueError:
        print("Invalid input. Please enter a valid range.")
        
# wait time between each api requests
while True:
    sleep_interval = input("Set sleep timer intervals in seconds for api request: ")
    if sleep_interval.isdigit():
        sleep_interval = int(sleep_interval)
        break
    else:
        print("Invalid input. Please enter a valid integer.")

# Set the headers to specify the content type
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# Define a function to sanitize a string for use as a folder name
def sanitize_for_folder_name(text):
    disallowed_chars = r'[\/:*?"<>|]' # Define a regular expression pattern to match disallowed characters
    sanitized_text = re.sub(disallowed_chars, '_', text) # Replace disallowed characters with underscores
    return sanitized_text

while True:
    try:
        for page_number in range(start, end + 1):
            params = {"limit": set_limit, "sort": "Newest", "nsfw": "true", "page": page_number}
            print(f"Parsing page: {page_number}")
            
            # Perform the GET request
            response = requests.get(api_url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])  # Get the "items" list

                def itemList(item):
                    model_id = item.get("id")
                    model_name = item.get("name")
                    model_description = item.get("description")
                    model_type = item.get("type")
                    model_creatorusername = item.get("creator", {}).get("username")
        
                    # Skips a specific model
                    if model_name == "400GB-LoRA-XL-Repository":
                        print(f"Model '{model_name}' found, skipping...")
                        return
                    
                    loop_count = 0
                    
                    # Access modelVersions data
                    model_versions = item.get("modelVersions", [])
                    for model_version in model_versions:
                        loop_count += 1
                        if loop_count >= 2:
                            break
                        model_modelVersionsmode = model_version.get("mode")
                        model_modelVersionsname = model_version.get("name")
                        model_modelVersionscreatedAt = model_version.get("createdAt")
                        model_modelVersionsdownloadUrl = model_version.get("downloadUrl")
                        model_modelVersionstrainedWords = model_version.get("trainedWords")
                        
                        if model_modelVersionsmode is not None:
                            if model_modelVersionsmode == "Archived":
                                print(f"URL '{model_modelVersionsdownloadUrl}' | '{model_name}' | '{model_modelVersionsname}' | '{model_modelVersionsmode}' is not available. Skipping...")
                                break
                            
                        # Read the lines from the log file and store them in a set for faster lookup
                        with open(log_parsed_downloads_URL_path, "r", encoding="utf-8") as log_file:
                            parsed_urls = set(line.strip() for line in log_file.readlines())
        
                        # Read the lines from the log file and store them in a set for faster lookup
                        with open(log_parsed_downloads_URL_images_path, "r", encoding="utf-8") as log_file_images:
                            parsed_urls_images = set(line.strip() for line in log_file_images.readlines())
                        
                        # store parsed image URLs in a list
                        imageUrlList = []
                        images_versions = model_version.get("images", [])
                        for index, images_version in enumerate(images_versions):
                            model_modelVersionsimagesurl = images_version.get("url")
                            model_modelVersionsimagesurl = model_modelVersionsimagesurl.replace("width=450/", "") # removes the width to get higher resolution image
                            if not model_modelVersionsimagesurl:
                                model_modelVersionsimagesurl = images_version.get("url")
                            imageUrlList.append(model_modelVersionsimagesurl)
                        
                        # check imageUrlList list of urls against the parsed_urls_images url text file
                        imageInURLs = False
                        for imageURLs in imageUrlList: 
                            if imageURLs in parsed_urls_images:
                                imageInURLs = True

                        skip_file_download = False
                        # Skip model if download URL already exists in log file
                        if model_modelVersionsdownloadUrl in parsed_urls and imageInURLs is True: 
                            print(f"URL '{model_modelVersionsdownloadUrl}' | '{model_name}' | '{model_modelVersionsname}' has already been parsed. Skipping...")
                            continue
                        elif model_modelVersionsdownloadUrl in parsed_urls and imageInURLs is False: 
                            skip_file_download = True
                            print(f"URL '{model_modelVersionsdownloadUrl}' | '{model_name}' | '{model_modelVersionsname}' has already been parsed but image has not. Skipping model download only...")
                        
                        print(f"Model ID: {model_id}")
                        print(f"Model Name: {model_name}")
                        print(f"Model Type: {model_type}")
                        print(f"Model creator: {model_creatorusername}")
                        if model_description:
                            # Parse HTML content and decode with UTF-8 encoding
                            soup = BeautifulSoup(model_description, "html.parser")
                            parsed_description = soup.get_text()
                            decoded_description = parsed_description.encode("utf-8").decode("utf-8")
                            print(f"Model Description: {decoded_description}")
                        else:
                            decoded_description = ("")
                            print("Model Description is missing or empty.")
                        print(f"Model Version name: {model_modelVersionsname}")
                        print(f"Created At: {model_modelVersionscreatedAt}")
                        print(f"Download Url: {model_modelVersionsdownloadUrl}")
                        print(fr"Model post Url: https://civitai.com/models/{model_id}")
                        print(f"Trigger Words: {model_modelVersionstrainedWords}")
                            
                        # Download and save the file with its original filename using content-disposition header
                        if model_modelVersionsdownloadUrl and skip_file_download != True:
                            response_file = requests.get(model_modelVersionsdownloadUrl, headers=headers, stream=True)
                            if response_file.status_code == 200:
                                max_attempts = 3
                                delay_between_attempts = 1
                                attempts = 0
                                while attempts < max_attempts:
                                    # Extract filename from content-disposition header
                                    content_disposition = response_file.headers.get('content-disposition')
                                    if content_disposition:
                                        print("content_disposition true")
                                        file_name = content_disposition.split("filename=")[1].strip('"; ').encode('iso-8859-1').decode('utf-8')
                                        file_name_without_extension = os.path.splitext(file_name)[0] # Remove the file extension from file_name
                                        file_name = sanitize_for_folder_name(file_name)
                                        file_name_without_extension = sanitize_for_folder_name(file_name_without_extension)
                                        break
                                    else:
                                        # If content-disposition is not provided, retry after a delay
                                        attempts += 1
                                        print (f"Retrying to get file name content-disposition, attempt {attempts}")
                                        time.sleep(delay_between_attempts)
                                else:
                                    # If content-disposition is not provided, use a default name
                                    model_name = sanitize_for_folder_name(model_name)
                                    model_modelVersionsname = sanitize_for_folder_name(model_modelVersionsname)
                                    file_name = f"{model_name} - {model_modelVersionsname}"
                                    file_name_without_extension = f"{model_name} - {model_modelVersionsname}"
                                 
                                file_path = os.path.join(download_directory, file_name)
                                text_path = Path(fr"{download_directory}\{file_name_without_extension}.txt")
                                
                                #checks if current file with same file_name exists, if true then append a number
                                exist_count = 0
                                while os.path.exists(file_path):
                                    exist_count += 1
                                    exist_count_str = str(exist_count)
                                    file_name = f"{file_name} ({exist_count_str})"
                                    file_name_without_extension = f"{file_name_without_extension} {exist_count_str}"
                                    file_path = os.path.join(download_directory, file_name)
                                    text_path = Path(fr"{download_directory}\{file_name_without_extension}.txt")
                                    
                                # Create the directory if it doesn't exist
                                os.makedirs(download_directory, exist_ok=True)

                                while True:
                                    try:
                                        total_size_in_bytes= int(response_file.headers.get('content-length', 0))
                                        chunk_size = 1000 * 1000 #1000 Kilobytes
                                        progress_bar = tqdm(total=total_size_in_bytes, unit='B', unit_divisor=1000, unit_scale=True)
                                        with open(file_path, "wb") as file:
                                            for data in response_file.iter_content(chunk_size):
                                                file.write(data)
                                                progress_bar.update(len(data))
                                        progress_bar.close()
                                        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                                            print("ERROR, something went wrong")
                                        print(f"Downloaded file to: {file_path}")
                                        break
                                    except Exception as e:
                                        print(f"An error occurred: {str(e)}")
                                        for i in range(10, -1, -1):
                                            print(f"Retrying in: {i} seconds", end='\r')  # Clear the previous line
                                            time.sleep(1)
                            else:
                                print(f"Failed to download file: {model_modelVersionsdownloadUrl} Status code: {response_file.status_code}")
                                break
                        elif model_modelVersionsdownloadUrl:
                            print("Skipping model file download")
                            try:
                                response_file = requests.get(model_modelVersionsdownloadUrl, headers=headers, stream=True)
                                if response_file.status_code == 200:
                                    max_attempts = 3
                                    delay_between_attempts = 1
                                    attempts = 0
                                    while attempts < max_attempts:
                                        # Extract filename from content-disposition header
                                        content_disposition = response_file.headers.get('content-disposition')
                                        if content_disposition:
                                            file_name = content_disposition.split("filename=")[1].strip('"; ').encode('iso-8859-1').decode('utf-8')
                                            file_name_without_extension = os.path.splitext(file_name)[0] # Remove the file extension from file_name
                                            break
                                        else:
                                            # If content-disposition is not provided, retry after a delay
                                            attempts += 1
                                            print (f"Retrying to get file name content-disposition, attempt {attempts}")
                                            time.sleep(delay_between_attempts)
                                    else:
                                        # If content-disposition is not provided, use a default name
                                        file_name = f"{model_name} - {model_modelVersionsname}"
                                        file_name_without_extension = f"{model_name} - {model_modelVersionsname}"
                                        
                                    file_path = os.path.join(download_directory, file_name)
                                    text_path = Path(fr"{download_directory}\{file_name_without_extension}.txt")
                                else:
                                    print(f"Failed to download file: {model_modelVersionsdownloadUrl}")
                                    break
                            except Exception as e:
                                print(f"An unexpected error has occured {str(e)}")
                                break
                        else:
                            print("Could not download model URL, skipping....")
                            break
                        # Access files and images within the model_version loop
                        files_versions = model_version.get("files", [])
                        for files_version in files_versions:
                            model_modelVersionsfilessizeKb = files_version.get("sizeKB")
                            print(f"Model file size Kb: {model_modelVersionsfilessizeKb}")
                        
                        images_versions = model_version.get("images", [])
                        for index, images_version in enumerate(images_versions):
                            model_modelVersionsimagesurl = images_version.get("url")
                            model_modelVersionsimagesurl = model_modelVersionsimagesurl.replace("width=450/", "") # removes the width to get higher resolution image
                            if model_modelVersionsimagesurl:
                                print (f"Model version image URL: {model_modelVersionsimagesurl}")
                                image_name = os.path.basename(model_modelVersionsimagesurl)
                                image_extension = os.path.splitext(image_name)[1]  # Get the file extension
                                
                                # Create a new image name based on the file_name
                                image_name = f"{file_name_without_extension} ({index}){image_extension}"
                                image_path = os.path.join(download_directory, image_name)
                                
                                # Create the directory if it doesn't exist
                                os.makedirs(download_directory, exist_ok=True)
                                
                                image_count_attempts = 0
                                while True:
                                    image_count_attempts += 1
                                    response_image = requests.get(model_modelVersionsimagesurl, headers=headers, stream=True)
                                    if response_image.status_code == 200:
                                        if image_count_attempts <= 5:
                                            total_size_in_bytes= int(response_image.headers.get('content-length', 0))
                                            chunk_size = 1000 * 1000 #1000 Kilobytes
                                            progress_bar = tqdm(total=total_size_in_bytes, unit='B', unit_divisor=1000, unit_scale=True)
                                            with open(image_path, "wb") as image_file:
                                                for data in response_image.iter_content(chunk_size):
                                                    progress_bar.update(len(data))
                                                    image_file.write(data)
                                            progress_bar.close()
                                            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                                                print("ERROR, something went wrong")
                                            print(f"Downloaded image to: {image_path}")
                                            break    
                                        else:
                                            break
                                    else:
                                        if image_count_attempts <= 5:
                                            print(f"Failed to download image: {model_modelVersionsimagesurl}")
                                            for i in range(10, -1, -1):
                                                print(f"Retrying in: {i} seconds", end='\r')  # Clear the previous line
                                                time.sleep(1)
                                        else:
                                            break
                                break # Remove this break if you want it to download all images of the model version
                            else: #try for lower res image
                                model_modelVersionsimagesurl = images_version.get("url")
                                print (f"Model version image URL: {model_modelVersionsimagesurl}")
                                image_name = os.path.basename(model_modelVersionsimagesurl)
                                image_extension = os.path.splitext(image_name)[1]  # Get the file extension
                                
                                # Create a new image name based on the file_name
                                image_name = f"{file_name_without_extension} ({index}){image_extension}"
                                image_path = os.path.join(download_directory, image_name)
                                
                                # Create the directory if it doesn't exist
                                os.makedirs(download_directory, exist_ok=True)
                                
                                image_count_attempts = 0
                                while True:
                                    image_count_attempts += 1
                                    response_image = requests.get(model_modelVersionsimagesurl)
                                    if response_image.status_code == 200:
                                        if image_count_attempts <= 5:
                                            total_size_in_bytes= int(response_image.headers.get('content-length', 0))
                                            chunk_size = 1024 #1 Kilobytes
                                            progress_bar = tqdm(total=total_size_in_bytes, unit='B', unit_scale=True)
                                            with open(image_path, "wb") as image_file:
                                                for data in response_image.iter_content(chunk_size):
                                                    progress_bar.update(len(data))
                                                    image_file.write(data)
                                            progress_bar.close()
                                            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                                                print("ERROR, something went wrong")
                                            print(f"Downloaded image to: {image_path}")
                                        else:
                                            break
                                    else:
                                        if image_count_attempts <= 5:
                                            print(f"Failed to download image: {model_modelVersionsimagesurl}")
                                            for i in range(10, -1, -1):
                                                print(f"Retrying in: {i} seconds", end='\r')  # Clear the previous line
                                                time.sleep(1)
                                        else:
                                            break
                                break # Remove this break if you want it to download all images of the model version

                        if skip_file_download != True:
                            with log_parsed_downloads_URL_path.open(mode='a', encoding='utf-8') as f:
                                f.write(f"{model_modelVersionsdownloadUrl}\n")
        
                        with log_parsed_downloads_URL_images_path.open(mode='a', encoding='utf-8') as f:
                            f.write(f"{model_modelVersionsimagesurl}\n")
                        
                        if not model_modelVersionsimagesurl:
                            model_modelVersionsimagesurl = "N/A"
                        
                        if skip_file_download != True:
                            with text_path.open(mode='a', encoding='utf-8') as f:
                                f.write(f"Model Name: {model_name}\n"
                                f"Model Version name: {model_modelVersionsname}\n"
                                f"Model creator: {model_creatorusername}\n"
                                f"Model Type: {model_type}\n"
                                f"Model ID: {model_id}\n"
                                f"Model Description: {decoded_description}\n"
                                f"Created At: {model_modelVersionscreatedAt}\n"
                                f"Download Url: {model_modelVersionsdownloadUrl}\n"
                                f"Image Download Url: {model_modelVersionsimagesurl}\n"
                                f"Trigger Words: {model_modelVersionstrainedWords}\n"
                                f"Model file size Kb: {model_modelVersionsfilessizeKb}\n"
                                fr"Model post Url: https://civitai.com/models/{model_id}""\n"
                                )
                    print("-" * 100)
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel_tasks) as executor:
                    futures = [executor.submit(itemList, item) for item in items]
                    concurrent.futures.wait(futures)
            else:
                print(f"Failed to fetch data. Status code: {response.status_code}")
        print(f"Sleeping for {sleep_interval} seconds")
        for i in range(sleep_interval, -1, -1):
            print(f"Time remaining before continuing: {i} seconds", end='\r')  # Clear the previous line
            time.sleep(1)
    except Exception as e:
        print(f"An unexpected error has occured {str(e)}")
        print(f"Sleeping for {sleep_interval} seconds")
        for i in range(sleep_interval, -1, -1):
            print(f"Time remaining before continuing: {i} seconds", end='\r')  # Clear the previous line
            time.sleep(1)
        continue
