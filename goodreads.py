import csv
import os

from bs4 import BeautifulSoup as bs
import requests
import io
from PIL import Image
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Accept-Language": "en-US, en;q=0.5",
}


def download_image(download_path, image_url, file_name):
    # create the download_path if it does not exist
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    # skip if image other than jpg
    if not image_url.lower().endswith('.jpg'):
        print('Skip download as image not a JPEG')
        return

    image_content = requests.get(image_url).content
    image_file = io.BytesIO(image_content)
    image = Image.open(image_file)

    # convert the image to RGB mode if it has an alpha channel
    if image.mode == 'RGBA':
        image = image.convert('RGB')

    file_path = download_path + file_name

    with open(file_path, 'wb') as f:
        image.save(f, 'JPEG')

    print("Image Downloaded")


def clean_string(string):
    cleaned = re.sub(r'\s+', ' ', string).strip()
    return cleaned


def get_ratings_reviews(text):
    # Find the substring for ratings
    ratings = text[:text.find(" ratings")].replace(",", "")

    # Find the substring for reviews
    reviews = text[text.find("and ") + 4:text.find(" reviews")].replace(",", "")

    return int(ratings), int(reviews)


app_url = "https://www.goodreads.com"
start_url = "https://www.goodreads.com/choiceawards/best-books-2024"

res = requests.get(start_url, headers=HEADERS)
soup = bs(res.text, 'html.parser')

categories = soup.select('.category')
# print(len(categories))

# for category in categories:
#     genre = category.select('h4.category__copy')[0].text.strip()
#     url = category.select('a')[0].get('href')
#     print(url)

books = []

# for category in categories:
for index, category in enumerate(categories):
    genre = category.select('h4.category__copy')[0].text.strip()
    url = category.select('a')[0].get('href')
    category_url = f"{app_url}{url}"
    print(category_url)

    res = requests.get(category_url, headers=HEADERS)
    soup = bs(res.text, 'html.parser')

    category_books = soup.select('.resultShown a.pollAnswer__bookLink')
    print(len(category_books))

    # for book in category_books[0:len(category_books)]:
    for book_index, book in enumerate(category_books):
        parent_tag = book.find_parent(class_='resultShown')
        votes = parent_tag.find(class_='result').text.strip()
        book_votes = clean_string(votes).split(" ")[0].replace(",", "")
        print("votes:", book_votes)

        book_url = book.get('href')
        book_url_formatted = f"{app_url}{book_url}"
        book_img = book.find('img')
        book_img_url = book_img.get('src')
        book_img_alt = book_img.get('alt')
        book_title = clean_string(book_img_alt)
        print(book_title)
        book_name = book_title.split('by')[0].strip()
        book_author = book_title.split('by')[1].strip()

        # Navigate to book url and get book and author details
        res = requests.get(book_url_formatted, headers=HEADERS)
        soup = bs(res.text, 'html.parser')

        book_rating = soup.find(class_="RatingStatistics__rating").text.strip()
        print(book_rating)

        book_ratings_reviews = soup.find(class_="RatingStatistics__meta").get('aria-label').strip()
        book_ratings, book_reviews = get_ratings_reviews(book_ratings_reviews)
        print(f"Ratings: {book_ratings}, Reviews: {book_reviews}")

        book_description_elements = soup.select('.BookPageMetadataSection__description .Formatted')
        if book_description_elements:
            book_description = book_description_elements[0].text
        else:
            book_description = 'No description found'

        author_avatar_url_element = soup.select('.PageSection .AuthorPreview a.Avatar img.Avatar__image')
        if author_avatar_url_element:
            author_avatar_url = author_avatar_url_element[0].get('src')
        else:
            author_avatar_url = 'No Avatar found'

        author_description_element = soup.select('.PageSection > .TruncatedContent .Formatted')
        if author_description_element:
            author_description = author_description_element[0].text
        else:
            author_description = 'No description found'

        print(author_description)

        bookPages = soup.select_one(".FeaturedDetails p[data-testid='pagesFormat']")
        if bookPages:
            pages_format = bookPages.text[:bookPages.text.find(" pages")]
        else:
            pages_format = "No pages found"
        print(pages_format)

        publication_info = soup.select_one(".FeaturedDetails p[data-testid='publicationInfo']")
        if publication_info:
            publication = publication_info.text[16:]
        else:
            publication = "No publication found"
        print(publication)

        # book_dict = {
        #     "title": book_name,
        #     "description": book_description,
        #     "author": {
        #         "name": book_author,
        #         "about": author_description,
        #         "avatar_url": author_avatar_url
        #     },
        #     "genre": genre,
        #     "pages": pages_format,
        #     "publication_info": publication,
        #     "img_url": book_img_url,
        #     "book_url": f"{app_url}{book_url}"
        # }

        book_dict = {
            "category": genre,
            "votes": book_votes,
            "title": book_name,
            "description": book_description,
            "author_name": book_author,
            "author_about": author_description,
            "avatar_url": author_avatar_url,
            "pages": pages_format,
            "rating": book_rating,
            "ratings": book_ratings,
            "reviews": book_reviews,
            "publication_info": publication,
            "img_url": book_img_url,
            "book_url": f"{app_url}{book_url}"
        }

        books.append(book_dict)

        print(book_img_url)
        # download_image("images/books/", book_img_url, f"{book_name}.jpg")

        print(author_avatar_url)
        # download_image("images/authors/", author_avatar_url, f"{book_author}.jpg")

        csv_filename = "books.csv"

        # check if first entry, write the header
        print("Index:", index)
        if index == 0 and book_index == 0:
            with open(csv_filename, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=book_dict.keys())
                writer.writeheader()

        with open(csv_filename, mode="a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=book_dict.keys())
            writer.writerow(book_dict)

        # json_filename = "books.json"
        # with open(json_filename, 'w') as json_file:
        #     json.dump(books, json_file, indent=4)
