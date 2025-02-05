from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
import time

# Replace with the path to your Edge WebDriver if not in PATH
driver = webdriver.Edge()

# URL of Discord web app
discord_url = 'https://discord.com/login'

# Credentials (you can replace this with environment variables for security)
email = 'kamil.gold01@gmail.com'
password = 'Wxcv@Kamil.1412004'

# List of categories and channels to create
categories_channels = {
    "Category 1": ["cours", "tds", "bonus", "exams"],
    "Category 2": ["cours", "tds", "bonus", "exams"],
}

# Function to log into Discord
def discord_login():
    driver.get(discord_url)
    
    # Allow page to load
    time.sleep(5)
    
    # Find and enter email
    email_input = driver.find_element(By.NAME, 'email')
    email_input.send_keys(email)
    
    # Find and enter password
    password_input = driver.find_element(By.NAME, 'password')
    password_input.send_keys(password)
    
    # Submit login
    password_input.send_keys(Keys.RETURN)
    
    # Allow time to log in
    time.sleep(10)  # Adjust time as needed to manually select the server


from selenium.webdriver import ActionChains

# Function to create a category
def create_category(category_name):
    # Wait for the sidebar to load
    sidebar = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "sidebar-class")]'))  # Adjust with the correct class or attribute
    )
    
    # Perform the right-click action
    actions = ActionChains(driver)
    actions.move_to_element(sidebar).context_click().perform()
    time.sleep(1)
    
    # Click on the "Create Category" option from the context menu
    create_category_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "Create Category")]'))
    )
    create_category_btn.click()
    time.sleep(2)
    
    # Enter the category name
    category_name_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Category Name"]'))
    )
    category_name_input.send_keys(category_name)
    time.sleep(1)
    
    # Confirm the creation
    confirm_btn = driver.find_element(By.XPATH, '//button[@type="submit"]')
    confirm_btn.click()
    time.sleep(2)
    
    print(f"Created category: {category_name}")


# Function to create a text channel within a category
def create_channel(channel_name, category_name):
    # Navigate to the category and click to create a channel within that category
    category_button = driver.find_element(By.XPATH, f'//div[@aria-label="{category_name}"]/following-sibling::button[@aria-label="Create Channel"]')
    category_button.click()
    
    # Select text channel option
    text_channel_option = driver.find_element(By.XPATH, '//div[@role="radiogroup"]//label[contains(text(), "Text")]')
    text_channel_option.click()
    
    # Enter the channel name
    channel_name_input = driver.find_element(By.XPATH, '//input[@placeholder="Channel Name"]')
    channel_name_input.send_keys(channel_name)
    
    # Confirm creation
    create_btn = driver.find_element(By.XPATH, '//button[@type="submit"]')
    create_btn.click()
    time.sleep(2)
    
    print(f"Created channel: {channel_name} in category {category_name}")

# Main function to automate category and channel creation
def automate_discord():
    # Log into Discord
    discord_login()
    
    # Iterate over the categories and their channels
    for category, channels in categories_channels.items():
        create_category(category)
        for channel in channels:
            create_channel(channel, category)
    
    print("Automation complete!")

# Run the automation
automate_discord()

# Close the driver after work is done
driver.quit()
