import requests
from bs4 import BeautifulSoup
import csv

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

olx_urls = {
    'gdansk': 'https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/gdansk/?page=',
    'sopot': 'https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/sopot/?page=',
    'gdynia': 'https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/gdynia/?page='
}

def parse_location(location):
    if "-" in location:
        location = location.split("-")[0].strip()
    parts = location.split(", ")
    if len(parts) == 2:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], None
    return None, None

def extract_area(area_text):
    try:
        area = area_text.split("m²")[0].strip()
        return area.replace(",", ".")
    except IndexError:
        return None

def extract_price(price_text):
    return price_text.split("zł")[0].strip().replace(" ", "")

def get_max_page(soup):
    page_elements = soup.find_all('li', {'data-testid': 'pagination-list-item'})
    max_page = 1
    for elem in page_elements:
        try:
            page_num = int(elem.text.strip())
            max_page = max(max_page, page_num)
        except ValueError:
            continue
    return max_page

def save_to_csv(filename, data):
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def scrape_olx_city(city, base_url):
    print(f"Scraping OLX listings for {city}...")
    all_listings = []
    page = 1

    url = f"{base_url}{page}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page 1 for {city}. HTTP Status Code: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    max_page = get_max_page(soup)
    print(f"Max pages for {city} on OLX: {max_page}")

    while page <= max_page:
        print(f"Scraping page {page} for {city}")
        url = f"{base_url}{page}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to fetch page {page} for {city}. HTTP Status Code: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        listings = soup.find_all('div', class_='css-l9drzq')

        if not listings:
            print(f"No more listings found on page {page} for {city}.")
            break

        page_data = []
        for listing in listings:
            title_elem = listing.select_one('h4.css-1s3qyje')
            price_elem = listing.select_one('p[data-testid="ad-price"].css-13afqrm')
            location_elem = listing.select_one('p.css-1mwdrlh')
            area_elem = listing.select_one('span.css-1cd0guq')

            title = title_elem.text.strip() if title_elem else "Brak tytułu"
            price = extract_price(price_elem.text.strip()) if price_elem else "Brak ceny"
            location = location_elem.text.strip() if location_elem else "Brak lokalizacji"
            area = extract_area(area_elem.text.strip()) if area_elem else "Brak metrażu"

            city_name, district = parse_location(location)

            page_data.append([title, price, city_name, district, area])

        save_to_csv(f"olx_{city}_listings.csv", page_data)
        all_listings.extend(page_data)
        page += 1

    print(f"Finished scraping OLX for {city}. Total listings: {len(all_listings)}")

def main():
    for city, base_url in olx_urls.items():
        filename = f"olx_{city}_listings.csv"
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Title", "Price (zł)", "City", "District", "Area (m²)"])
        scrape_olx_city(city, base_url)

if __name__ == "__main__":
    main()
