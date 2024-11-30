import requests
from bs4 import BeautifulSoup
import csv
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

trojmiasto_urls = {
    'gdansk': 'https://ogloszenia.trojmiasto.pl/nieruchomosci/gdansk/ikl,101_106,wi,100_200_230_250_260_220_240_210.html?page=',
    'sopot': 'https://ogloszenia.trojmiasto.pl/nieruchomosci/sopot/ikl,101_106,wi,100_200_230_250_260_220_240_210.html?page=',
    'gdynia': 'https://ogloszenia.trojmiasto.pl/nieruchomosci/gdynia/ikl,101_106,wi,100_200_230_250_260_220_240_210.html?page='
}

def parse_location(location):
    location = location.split(",")[0].strip()
    parts = location.split(" ")
    if len(parts) > 1:
        return parts[0], " ".join(parts[1:])
    return parts[0], None 

def extract_price(price_text):
    return price_text.split("zł")[0].strip().replace(" ", "")

def extract_area(area_text):
    try:
        return area_text.split("m²")[0].strip().replace(",", ".")
    except IndexError:
        return None

def get_max_page(soup):
    last_page_element = soup.select_one('a.pages__controls__last')
    if last_page_element and 'data-page-number' in last_page_element.attrs:
        return int(last_page_element['data-page-number'])
    return 1

def save_to_csv(filename, data):
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def fetch_page_with_retry(url, headers, retries=5, delay=5, backoff_factor=2):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                print(f"Rate limit reached. Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(delay)
                delay *= backoff_factor
            else:
                print(f"Failed with status code {response.status_code}. Retrying...")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}. Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
            time.sleep(delay)
            delay *= backoff_factor
        except requests.exceptions.Timeout:
            print(f"Timeout error. Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
            time.sleep(delay)
            delay *= backoff_factor
    print(f"Failed to fetch {url} after {retries} attempts.")
    return None

def scrape_trojmiasto_city(city, base_url):
    print(f"Scraping Trojmiasto listings for {city}...")
    all_listings = []
    page = 1

    url = f"{base_url}{page}"
    response = fetch_page_with_retry(url, headers=headers)

    if not response:
        print(f"Failed to fetch page 1 for {city}.")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    max_page = get_max_page(soup)
    print(f"Max pages for {city} on Trojmiasto: {max_page}")

    while page <= max_page:
        print(f"Scraping page {page} for {city}...")
        url = f"{base_url}{page}"
        response = fetch_page_with_retry(url, headers=headers)

        if not response:
            print(f"Failed to fetch page {page} for {city}. Skipping.")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        listings = soup.find_all('div', class_='list__item')

        if not listings:
            print(f"No more listings found on page {page} for {city}.")
            break

        page_data = []
        for listing in listings:
            title_elem = listing.select_one('a.list__item__content__title__name')
            price_elem = listing.select_one('p.list__item__price__value')
            location_elem = listing.select_one('p.list__item__content__subtitle')
            area_elem = listing.select_one('li.details--icons--element--powierzchnia p.list__item__details__icons__element__desc')

            title = title_elem['title'].strip() if title_elem else "Brak tytułu"
            price = extract_price(price_elem.text.strip()) if price_elem else "Brak ceny"
            location = location_elem.text.strip() if location_elem else "Brak lokalizacji"
            area = extract_area(area_elem.text.strip()) if area_elem else "Brak powierzchni"

            city_name, district = parse_location(location)

            page_data.append([title, price, city_name, district, area])

        save_to_csv(f"trojmiasto_{city}_listings.csv", page_data)
        all_listings.extend(page_data)

        time.sleep(0.5) 
        page += 1

    print(f"Finished scraping Trojmiasto for {city}. Total listings: {len(all_listings)}")

def main():
    for city, base_url in trojmiasto_urls.items():
        filename = f"trojmiasto_{city}_listings.csv"
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Title", "Price (zł)", "City", "District", "Area (m²)"])
        scrape_trojmiasto_city(city, base_url)

if __name__ == "__main__":
    main()
