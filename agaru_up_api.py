# main.py
from typing import List, Optional
from fastapi import FastAPI, Query, status
from pydantic import BaseModel

app = FastAPI()


# 動画検索時の返り値1件分の型
class Video(BaseModel):
    title: str
    tags: List[str]
    location: str
    baseUrl: str
    movieId: str

# アゲ報告用のリクエストボディ
class ReportRequest(BaseModel):
    user: str
    location: str

# 複数UUIDで動画を取得するリクエストボディ
class BulkVideosRequest(BaseModel):
    videos: List[str]



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

# 動画検索API
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

# アゲ報告API
@app.post("/report", status_code=status.HTTP_201_CREATED)
def report_agereport(report: ReportRequest):
    """
    アゲ報告API
    POST /report
    Body: {"user": "...", "location": "..."}
    """

    # 本来はここで DB に保存したりイベントを発行したりします。
    return {"message": "Report received", "user": report.user, "location": report.location}

# タグリスト一覧取得API
@app.get("/tags", response_model=List[str])
def list_tags():
    """
    タグ一覧取得API
    GET /tags
    """

    seen = set()
    tags: List[str] = []
    for v in MOCK_VIDEOS:
        for t in v.tags:
            if t not in seen:
                seen.add(t)
                tags.append(t)

    return tags

# uuid指定検索API
@app.post("/videos/bulk", response_model=List[Video])
def videos_bulk(request: BulkVideosRequest):
    """
    動画一括取得API
    POST /videos/bulk
    Body: {"videos": ["uuid1","uuid2", ...]}

    入力の順序と重複を維持して、見つかった動画を返します。
    見つからないUUIDはスキップします。
    """

    # movieId -> Video マッピングを作成
    id_map = {v.movieId: v for v in MOCK_VIDEOS}

    results: List[Video] = []
    for vid in request.videos:
        video = id_map.get(vid)
        if video:
            results.append(video)

    return results

