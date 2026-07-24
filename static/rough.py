# is_self:true
# gender:male
# medical_history:false
# consent_to_forward:false
# specialization:Pediatrician
# preferred_date:2025-08-20
# time_slot:19:00
# opinion_type:first
# appointment_type:normal
# doctor_id:DR202
# problem_description:string



# experience_years:10
# work_location:madhapur,500081
# doctor_name:girish
# clinic_location:madhapur,500081
# degree:Cardiologist
# about:software developer
# dm_amount:25000
# phone:9502506410
# specialization_id:5
# consultation_fee:2000
# address:hanuman juction
# password:123456
# email:girish@gmail.com

# import pandas as pd
# import requests
#
# # Example public Excel file URL
# url = "https://docs.google.com/spreadsheets/d/1MMU_bwnp_pDQhNTOeob0CuBUIF1gsBbXAWRVyznEEBs/edit?usp=sharing"
#
# response = requests.get(url)
#
# print(response.text[:200])


# # Download file into memory
# response = requests.get(url)
# with open("temp.xlsx", "wb") as f:
#     f.write(response.content)
#
# # Read the downloaded file
# df = pd.read_excel("temp.xlsx", engine="openpyxl")
# print(df)

# import pandas as pd
# import requests
#
# # Direct Excel download URL
# url = "https://docs.google.com/spreadsheets/d/1MMU_bwnp_pDQhNTOeob0CuBUIF1gsBbXAWRVyznEEBs/export?format=xlsx"
#
# # Download the file
# response = requests.get(url)
# with open("sheet.xlsx", "wb") as f:
#     f.write(response.content)
#
# # Read Excel into pandas
# df = pd.read_excel("sheet.xlsx", engine="openpyxl")
# print(df)


import pandas as pd
import requests
from io import BytesIO
from urllib.parse import urlparse

def google_sheet_to_df(sheet_url):
    """
    Convert a Google Sheet URL to a pandas DataFrame
    """
    # Extract spreadsheet ID from URL
    parts = sheet_url.split('/')
    try:
        sheet_id_index = parts.index('d') + 1
        sheet_id = parts[sheet_id_index]
    except ValueError:
        raise ValueError("Invalid Google Sheet URL")

    # Create direct Excel download URL
    download_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

    # Download file into memory
    response = requests.get(download_url)
    if response.status_code != 200:
        raise Exception("Failed to download sheet. Make sure it is shared as 'Anyone with the link can view'.")

    # Read into pandas DataFrame
    df = pd.read_excel(BytesIO(response.content), engine="openpyxl")
    return df

# Example usage
url = "https://docs.google.com/spreadsheets/d/1MMU_bwnp_pDQhNTOeob0CuBUIF1gsBbXAWRVyznEEBs/edit?usp=sharing"
df = google_sheet_to_df(url)
print(df)
