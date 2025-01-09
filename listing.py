class ListingValidationError(Exception):
    pass

class Listing:
    def __init__(self, title, price, city, district, area, url):
        self.title = title
        self.price = price
        self.city = city
        self.district = district
        self.area = area
        self.url = url

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = str(value).strip() if value else None

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        try:
            if value is None or value == "":
                self._price = None
                return
            self._price = int(float(str(value).replace(" ", "").replace("zł", "").replace(",", ".").strip()))
            if self._price < 0:
                raise ListingValidationError("Price cannot be negative")
        except ValueError:
            raise ListingValidationError(f"Invalid price format: {value}")

    @property
    def city(self):
        return self._city

    @city.setter
    def city(self, value):
        self._city = str(value).strip() if value else None

    @property
    def district(self):
        return self._district

    @district.setter
    def district(self, value):
        self._district = str(value).strip() if value else None

    @property
    def area(self):
        return self._area

    @area.setter
    def area(self, value):
        try:
            if value is None:
                self._area = None
                return
            self._area = float(str(value).replace(",", ".").replace("m²", "").replace(" ", "").replace("m2", "").strip())
            if self._area <= 0:
                raise ListingValidationError("Area must be positive")
        except ValueError:
            raise ListingValidationError(f"Invalid area format: {value}")
        
    @property
    def url(self):
        return self._url
    
    @url.setter
    def url(self, value):
        self._url = str(value).strip() if value else None

    def __str__(self):
        return f"{self.title} | {self.price} zł | {self.city} | {self.district} | {self.area} m²"

    def to_tuple(self):
        return (self.title, self.price, self.city, self.district, self.area)

    def to_dict(self):
        return {
            "title": self.title,
            "price": self.price,
            "city": self.city,
            "district": self.district,
            "area": self.area
        }