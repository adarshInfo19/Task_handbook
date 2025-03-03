import os
import os.path
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
import json
import boto3

s3=boto3.client("s3",region_name="ap-south-1")

# Create downloads directory
default_downloads_path = os.path.join(os.getcwd(), "temp")
if not os.path.isdir(default_downloads_path):
    os.mkdir(default_downloads_path)

class GreytHR:
    def __init__(self):
        self.browser = None
        self.delay = 15

    def login(self, USER_ID, PASSWORD):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Set download directory
            chrome_prefs = {"download.default_directory": default_downloads_path}
            chrome_options.add_experimental_option("prefs", chrome_prefs)

            self.browser = webdriver.Chrome(options=chrome_options)

            self.browser.maximize_window()  # Maximize window to ensure elements are visible

            self.browser.get("https://infocuspinnovations.greythr.com/uas/portal/auth/login")

            # Wait for username field
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.ID, "username"))
            )

            # Login process
            user_field = self.browser.find_element(by=By.ID, value="username")
            user_field.clear() 
            user_field.send_keys(str(USER_ID)) 

            password_field = self.browser.find_element(by=By.ID, value="password")
            password_field.clear()  
            password_field.send_keys(PASSWORD)

            # Click login button
            login_button = WebDriverWait(self.browser, self.delay).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "button[type='submit']"
                ))
            )
            login_button.click()

            # Wait for successful login
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "body > app > ng-component > div > gt-topbar > nav > div:nth-child(4) > a > div"
                ))
            )

        except TimeoutException as e:
            print(f"Timeout while trying to log in: {str(e)}")
            if self.browser:
                self.browser.quit()
            raise
        except WebDriverException as e:
            print(f"WebDriver error: {str(e)}")
            if self.browser:
                self.browser.quit()
            raise
        except Exception as e:
            print(f"Unexpected error during login: {str(e)}")
            if self.browser:
                self.browser.quit()
            raise

    def get_cookies(self):
        """Extract cookies from the browser session"""
        try:
            if not self.browser:
                raise Exception("Browser session not initialized")
            cookie = self.browser.get_cookies()
            return {c["name"]: c["value"] for c in cookie}
        except Exception as e:
            print(f"Error getting cookies: {str(e)}")
            return {}
        
    
    def get_joining_dates(self, data, cookie):
        url = "https://infocuspinnovations.greythr.com/v3/api/empinfo/empdir/"
        for emp in data:
            response = requests.get(url + str(emp["greythrid"]), cookies=cookie)
            if response.status_code == 200:
                joining_date = response.json()["fields"][0]["value"]
                emp["joining_date"] = joining_date
            else:
                print("Failed with status code:", response.status_code)

    def send_api_req(self, cookies):
        """Fetch employee data from the GreytHR API"""
        try:
            url = "https://infocuspinnovations.greythr.com/v3/api/employee/list?page=1&pageSize=200"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.post(url, json={}, cookies=cookies, headers=headers)
            
            response.raise_for_status()  # Raise an exception for bad status codes
            
            employees = response.json().get("results", [])
            return [
                {
                    "employeeid": emp["employeeno"],
                    "name": emp["name"],
                    "greythrid": emp["employeeid"],
                }
                for emp in employees
            ]
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            print(f"Failed to parse API response: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error in API request: {str(e)}")
            return []

    def get_all_employee_data(self, USER_ID, PASSWORD):
        """Login and fetch employee data"""
        try:
            print("Attempting login...")
            self.login(USER_ID, PASSWORD)
            print("Successfully logged in.")

            cookies = self.get_cookies()
            if not cookies:
                raise Exception("Failed to get cookies after login")

            data = self.send_api_req(cookies)
            if not data:
                print("Warning: No employee data retrieved")

            return data, cookies

        except Exception as e:
            print(f"Error in get_all_employee_data: {str(e)}")
            return [], {}
        finally:
            if self.browser:
                self.browser.quit()



def lambda_trigger():
    try:

        greyt_hr_obj = GreytHR()
        all_greyhr_emp, cookies = greyt_hr_obj.get_all_employee_data("Userid", "Password")


        json_string = json.dumps(all_greyhr_emp, indent=2)

        bucket_name = "jsondatacollector"
        object_key = "employees2/employee_data.json"

        s3.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=json_string,
            ContentType='application/json'
        )

        print("employee data successfully uplocaded to the s3")
        return {
                "statusCode": 200,
                "body": json.dumps({"message": "Employee data upload successful!"})
            }
    except Exception as err:
        print("Error while uploading employee data to S3:", err)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to upload employee data to S3"})
        }

