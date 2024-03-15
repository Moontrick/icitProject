from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from app import index
from app.context import ctx

router = APIRouter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ctx.make_directory()
    ctx.init_visited_pages()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.post("/scrapedImg")
async def scrapeImages(imageCount: int):
    await index.main(startUrl=ctx.startUrl,
                     directory=ctx.directory,
                     imageCount=imageCount,
                     visitedUrls=ctx.visitedPages,
                     nextUrl=ctx.startUrl,
                     visitedPageData=ctx.visitedPageData)
    return {"message": "scraping is successful"}
