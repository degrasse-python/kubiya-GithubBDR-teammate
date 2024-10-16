import os
import time
import re
import json
from datetime import datetime
from typing import List, Dict, Type

import pandas as pd
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, create_model
import html2text
import tiktoken

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from openai import OpenAI
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

SBR_WEBDRIVER=os.environ.get("SBR_WEBDRIVER")
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')

model = OllamaLLM(model="llama3")

# Set up the Chrome WebDriver options
def setup_selenium():
  options = Options()

  # adding arguments
  options.add_argument("--disable-gpu")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("--headless=new")
  
  # Randomize user-agent to mimic different users -- internet search for the user agent
  options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.3")
  # Specify the path to the ChromeDriver
  service = Service(SBR_WEBDRIVER)  

  # Initialize the WebDriver
  driver = webdriver.Chrome(service=service, options=options)
  return driver

def fetch_html_selenium(url):
  driver = setup_selenium()
  try:
    driver.get(url)
    
    # Add random delays to mimic human behavior
    time.sleep(5)  # Adjust this to simulate time for user to read or interact
    
    # Add more realistic actions like scrolling
    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)  # Simulate time taken to scroll and read
    
    html = driver.page_source
    return html
  finally:
    driver.quit()

def clean_html(html_content):
  # extract_body_content by removing header and footer
  soup = BeautifulSoup(html_content, 'html.parser')
  
  # Remove headers and footers based on common HTML tags or classes
  for element in soup.find_all(['header', 'footer']):
    element.decompose()  # Remove these tags and their content

  return str(soup)


def html_to_markdown_with_readability(html_content):
  cleaned_html = clean_html(html_content)  
  
  # Convert to markdown
  markdown_converter = html2text.HTML2Text()
  markdown_converter.ignore_links = False
  markdown_content = markdown_converter.handle(cleaned_html)
  
  return markdown_content

# Define the pricing for gpt-4o-mini without Batch API
pricing = {
  "gpt-4o-mini": {
      "input": 0.150 / 1_000_000,  # $0.150 per 1M input tokens
      "output": 0.600 / 1_000_000, # $0.600 per 1M output tokens
  },
  "gpt-4o-2024-08-06": {
      "input": 2.5 / 1_000_000,  # $0.150 per 1M input tokens
      "output": 10 / 1_000_000, # $0.600 per 1M output tokens
  },
  # Add other models and their prices here if needed
  }

model_used='gpt-3.5-turbo' #"gpt-4o-mini"
    
def save_raw_data(raw_data, timestamp, output_folder='output'):
  # Ensure the output folder exists
  os.makedirs(output_folder, exist_ok=True)
  
  # Save the raw markdown data with timestamp in filename
  raw_output_path = os.path.join(output_folder, f'rawData_{timestamp}.txt')
  with open(raw_output_path, 'w', encoding='utf-8') as f:
    f.write(raw_data)
  print(f"Raw data saved to {raw_output_path}")
  return raw_output_path


def remove_urls_from_file(file_path):
  # Regex pattern to find URLs
  url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

  # Construct the new file name
  base, ext = os.path.splitext(file_path)
  new_file_path = f"{base}_cleaned{ext}"

  # Read the original markdown content
  with open(file_path, 'r', encoding='utf-8') as file:
    markdown_content = file.read()

  # Replace all found URLs with an empty string
  cleaned_content = re.sub(url_pattern, '', markdown_content)

  # Write the cleaned content to a new file
  with open(new_file_path, 'w', encoding='utf-8') as file:
    file.write(cleaned_content)
  print(f"Cleaned file saved as: {new_file_path}")
  return cleaned_content


def create_dynamic_listing_model(field_names: List[str]) -> Type[BaseModel]:
  """
  Dynamically creates a Pydantic model based on provided fields.
  field_name is a list of names of the fields to extract from the markdown.
  """
  # Create field definitions using aliases for Field parameters
  field_definitions = {field: (str, ...) for field in field_names}
  # Dynamically create the model with all field
  return create_model('DynamicListingModel', **field_definitions)


def create_listings_container_model(listing_model: Type[BaseModel]) -> Type[BaseModel]:
  """
  Create a container model that holds a list of the given listing model.
  """
  return create_model('DynamicListingsContainer', listings=(List[listing_model], ...))


def trim_to_token_limit(text, model, max_tokens=200000):
  encoder = tiktoken.encoding_for_model(model)
  tokens = encoder.encode(text)
  if len(tokens) > max_tokens:
    trimmed_text = encoder.decode(tokens[:max_tokens])
    return trimmed_text
  return text

def format_data(data, DynamicListingsContainer):



  client = OpenAI(api_key=OPENAI_API_KEY)

  system_message = """You are an intelligent text extraction and conversion assistant. Your task is to extract structured information 
                      from the given text and convert it into a pure JSON format. The JSON should contain only the structured data extracted from the text, 
                      with no additional commentary, explanations, or extraneous information. 
                      You could encounter cases where you can't find the data of the fields you have to extract or the data will be in a foreign language.
                      Please process the following text and provide the output in pure JSON format with no words before or after the JSON:"""

  user_message = f"Extract the following information from the provided text:\nPage content:\n\n{data}"

  completion = client.beta.chat.completions.parse(
                model=model_used,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                response_format=DynamicListingsContainer
  )
  return completion.choices[0].message.parsed
    

def parse_with_ollama(dom_chunks, parse_description):
    
  template = (
              "You are tasked with extracting specific information from the following text content: {dom_content}. "
              "Please follow these instructions carefully: \n\n"
              "1. **Extract Information:** Only extract the information that directly matches the provided description: {parse_description}. "
              "2. **No Extra Content:** Do not include any additional text, comments, or explanations in your response. "
              "3. **Empty Response:** If no information matches the description, return an empty string ('')."
              "4. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text."
            )
  prompt = ChatPromptTemplate.from_template(template)
  chain = prompt | model

  parsed_results = []

  for i, chunk in enumerate(dom_chunks, start=1):
    response = chain.invoke(
        {"dom_content": chunk, "parse_description": parse_description}
    )
    print(f"Parsed batch: {i} of {len(dom_chunks)}")
    parsed_results.append(response)

  return "\n".join(parsed_results)


def save_formatted_data(formatted_data, timestamp, output_folder='output'):
  # Ensure the output folder exists
  os.makedirs(output_folder, exist_ok=True)
  
  # Prepare formatted data as a dictionary
  formatted_data_dict = formatted_data.dict() if hasattr(formatted_data, 'dict') else formatted_data

  # Save the formatted data as JSON with timestamp in filename
  json_output_path = os.path.join(output_folder, f'sorted_data_{timestamp}.json')
  with open(json_output_path, 'w', encoding='utf-8') as f:
    json.dump(formatted_data_dict, f, indent=4)
  print(f"Formatted data saved to JSON at {json_output_path}")

  # Prepare data for DataFrame
  if isinstance(formatted_data_dict, dict):
    # If the data is a dictionary containing lists, assume these lists are records
    data_for_df = next(iter(formatted_data_dict.values())) if len(formatted_data_dict) == 1 else formatted_data_dict
  elif isinstance(formatted_data_dict, list):
    data_for_df = formatted_data_dict
  else:
    raise ValueError("Formatted data is neither a dictionary nor a list, cannot convert to DataFrame")

  # Create DataFrame
  try:
    df = pd.DataFrame(data_for_df)
    print("DataFrame created successfully.")

    # Save the DataFrame to an Excel file
    excel_output_path = os.path.join(output_folder, f'sorted_data_{timestamp}.xlsx')
    df.to_excel(excel_output_path, index=False)
    print(f"Formatted data saved to Excel at {excel_output_path}")
    
    return df
  except Exception as e:
    print(f"Error creating DataFrame or saving Excel: {str(e)}")
    return None

def calculate_price(input_text, output_text, model=model_used):
  # Initialize the encoder for the specific model
  encoder = tiktoken.encoding_for_model(model)
  
  # Encode the input text to get the number of input tokens
  input_token_count = len(encoder.encode(input_text))
  
  # Encode the output text to get the number of output tokens
  output_token_count = len(encoder.encode(output_text))
  
  # Calculate the costs
  input_cost = input_token_count * pricing[model]["input"]
  output_cost = output_token_count * pricing[model]["output"]
  total_cost = input_cost + output_cost
  
  return input_token_count, output_token_count, total_cost

def ExtractLinkedinURL(txtfile):
  pattern = r'linkedin[^/]+/in/[^/]+'
  with open(txtfile) as file:
    for line in file:
      result = re.search(pattern, line)
      if result:
        if len(result[0]) > 16:
          print(result[0])
          return result[0]
        
def GetLinkedinURL(markdown):
  pattern = r'linkedin[^/]+/in/[^/]+'
  result = re.search(pattern, markdown)
  print(result)
  return result[0]

# Buttons to trigger scraping
# Define the scraping function
def perform_scrape(url):
  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  raw_html = fetch_html_selenium(url)
  markdown = html_to_markdown_with_readability(raw_html)
  linkedin_url = GetLinkedinURL(markdown)
  print(linkedin_url)
  # save_raw_data(markdown, timestamp)
  
  # result = re.match(pattern, markdown)
  DynamicListingModel = create_dynamic_listing_model(fields)
  DynamicListingsContainer = create_listings_container_model(DynamicListingModel)
  formatted_data = format_data(markdown, DynamicListingsContainer)
  print(formatted_data)
  formatted_data_text = json.dumps(formatted_data.dict())
  input_tokens, output_tokens, total_cost = calculate_price(markdown, formatted_data_text, model=model_selection)
  
  df = save_formatted_data(formatted_data, timestamp)

  return df, formatted_data, markdown, input_tokens, output_tokens, total_cost, timestamp




if __name__ == "__main__":
  url = 'https://github.com/adityasharma7'

  try:
    # # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # Scrape data
    raw_html = fetch_html_selenium(url)
    markdown = html_to_markdown_with_readability(raw_html)
    linkedin_url = GetLinkedinURL(markdown)
    
  except Exception as e:
    print(f"An error occurred: {e}")
      

