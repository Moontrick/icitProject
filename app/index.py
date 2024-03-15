import logging
import os
import asyncio
import hashlib
from dotenv import load_dotenv
import httpx
import requests
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.model.database import ImageData

load_dotenv()
engine = create_async_engine(os.getenv("URL_DATABASE"))
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, future=True)


async def saveImgToFolder(image, directory):
    checksum = hashlib.md5(image).hexdigest()

    imgPath = os.path.join(directory, f"{checksum}.jpg")
    with open(imgPath, "wb") as f:
        f.write(image)

    async with async_session.begin() as session:
        dbData = ImageData(id=checksum, imgsrc=imgPath)
        session.add(dbData)
        await session.commit()

async def saveImg(url, directory, semaphoreTask):
    async with semaphoreTask:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)

            if response.status_code == 200:
                await saveImgToFolder(response.content, directory)

async def scrappedImgUrl(html):
    soup = BeautifulSoup(html, 'html.parser')
    #find all img in page
    imageUrls = []
    for img in soup.find_all('img'):
        src = img.get('src')
        if src and (src.startswith('http://') or src.startswith('https://')) and src.endswith('.png'):
            imageUrls.append(src)

    return imageUrls



async def fetch(url):
    #so as not to ban IP with scrapping
    headers = {
        "Accept": "/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0",
        "Referer": "https://www.flaticon.com/ru/icon-fonts-most-downloaded"
    }
    req = requests.get(url, headers=headers)
    src = req.text
    return src


async def listeningPage(url, imageCount, directory):
    html = await fetch(url)
    image_urls = await scrappedImgUrl(html)

    tasks = []
    #create semaphoreTask
    semaphoreTask = asyncio.Semaphore(5)
    #take ONLY need count
    for img_url in image_urls[:imageCount]:
        tasks.append(saveImg(img_url, directory, semaphoreTask))

    currentNumber = imageCount - len(image_urls)
    if currentNumber < 0:
        currentNumber = 0

    await asyncio.gather(*tasks)
    return currentNumber


async def crawler(nextUrl, directory, visitedUrls, count, imageCount, startUrl, visitedPageData):
    curCount = imageCount
    if nextUrl not in visitedUrls: #if no visited page
        visitedUrls.add(nextUrl)
        curCount = await listeningPage(nextUrl, imageCount, directory)
        with open(visitedPageData, "a") as f:
            f.write(nextUrl + "\n")
    else:
        logging.info(f"This page visited. Try to find new page.")

    if curCount > 0:
        count += 1
        html = await fetch(nextUrl)
        soup = BeautifulSoup(html, 'html.parser')
        #find new page in a button href
        nextPage = soup.find("a", class_="pagination-next")
        if nextPage:
            next_url = nextPage.get("href")
            await crawler(next_url, directory, visitedUrls, count, curCount, startUrl, visitedPageData)
        else:
            logging.warning("Error with page found")
    else:
        logging.info("All images is downloaded")
        return


async def main(startUrl, directory, imageCount: int, visitedUrls, nextUrl, visitedPageData):

    if not os.path.exists(directory):
        os.makedirs(directory)

    await crawler(nextUrl, directory, visitedUrls, 1, imageCount, startUrl, visitedPageData)
