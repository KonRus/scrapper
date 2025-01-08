import requests
from bs4 import BeautifulSoup
import csv
import re
from listing import Listing
from sqlworker import DatabaseWorker

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

cities = {
    'gdansk': 'https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdansk?page=',
    'sopot': 'https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/sopot?page=',
    'gdynia': 'https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia?page='
}

def parse_location(location):
    parts = location.split(", ")
    if location.lower().startswith("ul."):
        if len(parts) == 4:
            return parts[1], parts[2], parts[3]
    else:
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
    return None, None, None

def save_to_csv(city, data):
    filename = f"{city}_listings.csv"
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for row in data:
            writer.writerow(row)

def get_max_page(soup):
    """Znajduje maksymalną liczbę stron z elementów `li` o klasie `css-43nhzf`."""
    page_elements = soup.find_all('li', class_='css-43nhzf')
    max_page = 1
    for elem in page_elements:
        try:
            page_num = int(elem.text.strip())
            max_page = max(max_page, page_num)
        except ValueError:
            continue
    return max_page

def clean_price(price):
    """Funkcja do usuwania złotówek i zostawiania tylko cyfr."""
    cleaned_price = re.sub(r'\D', '', price)
    return cleaned_price if cleaned_price else ''

def clean_surface(surface):
    """Funkcja do usuwania 'm2' z powierzchni."""
    cleaned_surface = surface.replace(' m²', '').strip()
    return cleaned_surface if cleaned_surface else ''

def scrape_city(city, base_url):
    print(f"Scraping listings for {city}...")
    db = DatabaseWorker()
    all_listings = 0
    page = 1

    first_url = f"{base_url}{page}"
    response = requests.get(first_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch initial page for {city}. HTTP Status Code: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    max_page = get_max_page(soup)
    print(f"Max pages for {city}: {max_page}")

    while page <= max_page:
        print(f"Scraping page {page} for {city}")
        url = f"{base_url}{page}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to fetch page {page} for {city}. HTTP Status Code: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        listings = soup.find_all('article', class_='css-136g1q2')

        if not listings:
            print(f"No more listings found on page {page} for {city}.")
            break

        page_data = []
        for listing in listings:
            title_elem = listing.find('p', class_='css-u3orbr e1g5xnx10')
            price_elem = listing.find('span', class_="css-2bt9f1 evk7nst0")
            location_elem = listing.find('p', class_='css-42r2ms eejmx80')

            title = title_elem.text.strip() if title_elem else "Brak tytułu"
            price = price_elem.text.strip() if price_elem else "Brak ceny"
            location = location_elem.text.strip() if location_elem else "Brak lokalizacji"

            dzielnica, miasto, wojewodztwo = parse_location(location)

            details_section = listing.find('dl', class_='css-12dsp7a')
            surface_area = "Brak danych"
            if details_section:
                dt_elements = details_section.find_all('dt')
                dd_elements = details_section.find_all('dd')
                for dt, dd in zip(dt_elements, dd_elements):
                    if dt.text.strip() == "Powierzchnia":
                        surface_area = dd.text.strip()
                        break

            price = clean_price(price)
            surface_area = clean_surface(surface_area)
            temp_listing = Listing(title, price, miasto, dzielnica, surface_area)

            page_data.append(temp_listing)

        db.upsert_listings(page_data, "otodom")
        all_listings += len(page_data)

        page += 1

    print(f"Finished scraping for {city}. Total listings: {all_listings}")
def main():
    for city, base_url in cities.items():
      scrape_city(city, base_url)

if __name__ == "__main__":
    main()
