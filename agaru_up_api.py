# main.py
from typing import List, Optional
from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI()


# 返り値1件分の型
class Video(BaseModel):
    title: str
    tags: List[str]
    location: str
    baseUrl: str
    movieId: str


# 仮のデータベース
MOCK_VIDEOS: List[Video] = [
    Video(
        title="過去一アガった瞬間！！",
        tags=["大阪駅", "tag2", "tag3"],
        location="camera1",
        baseUrl="https://21b073b9670215c4e64a2c3e6525f259.r2.cloudflarestorage.com/agaru-up-videos",
        movieId="uuid-example-1",
    ),
    Video(
        title="友達と過ごした最高の一日",
        tags=["梅田", "tag2"],
        location="camera2",
        baseUrl="https://21b073b9670215c4e64a2c3e6525f259.r2.cloudflarestorage.com/agaru-up-videos",
        movieId="uuid-example-2",
    ),
    Video(
        title="過去一アガった瞬間！！",
        tags=["大阪駅", "tag3"],
        location="camera3",
        baseUrl="https://21b073b9670215c4e64a2c3e6525f259.r2.cloudflarestorage.com/agaru-up-videos",
        movieId="uuid-example-3",
    ),
    # 必要に応じて追加
]

@app.get("/videos", response_model=List[Video])
def list_videos(
    q: Optional[str] = Query(None, description="検索ワード"),
    tags: Optional[str] = Query(
        None, description="タグ（カンマ区切り。例: 大阪駅,tag2）"
    ),
    limit: int = Query(10, ge=1, le=50, description="取得件数の上限"),
):
    """
    動画一覧取得API
    GET /videos?q=検索ワード&tags=タグ&limit=10
    """

    results = MOCK_VIDEOS

    # q（タイトル検索）
    if q:
        results = [v for v in results if q in v.title]

    # tags（AND条件でフィルタ）
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            results = [
                v for v in results
                if all(t in v.tags for t in tag_list)
            ]

    # limit 件だけ返す
    return results[:limit]
