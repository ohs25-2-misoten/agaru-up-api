from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Query, status, HTTPException
from pydantic import BaseModel

app = FastAPI()


# 動画検索時の返り値1件分の型
class Video(BaseModel):
    title: str
    tags: List[str]
    location: str
    generateDate: datetime
    baseUrl: str
    movieId: str
    url: str


# アゲ報告用のリクエストボディ
class ReportRequest(BaseModel):
    user: str
    location: str

# 複数UUIDで動画を取得するリクエストボディ
class BulkVideosRequest(BaseModel):
    videos: List[str]


# カメラ位置情報
class Coordinate(BaseModel):
    lat: float
    lng: float


# カメラ情報の型
class Camera(BaseModel):
    name: str
    id: str
    coordinate: Coordinate
    url: str

# 仮のデータベースパス（SQLite DB名：data.db）
DB_PATH = Path(__file__).parent / "data.db"


def get_conn():
        """
        SQLite 接続を返すヘルパー関数。

        - `DB_PATH` に指定されたファイルへ接続します。
        - 戻り値の接続オブジェクトは `row_factory` に `sqlite3.Row` を設定しており、
            カラム名でアクセスできる辞書風の行オブジェクトを返します。
        - 呼び出し元は使用後に `conn.close()` を呼んで接続を閉じてください。
        - このアプリは既存の SQLite DB を前提としています。DB ファイルが存在しない
            場合は接続時にエラーになります。
        """
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            # DB に接続できない場合は HTTP 503 を返す
            raise HTTPException(status_code=503, detail=f"DB unavailable: {e}")


def row_to_video(row: sqlite3.Row) -> Video:
    # DB の行 (Row) を Video モデルへ変換するヘルパー
    # - `tags` カラムはカンマ区切り文字列なのでリストへ分割する
    # - `createdAt` を datetime に変換して `generateDate` にセットする
    # - `url` は `baseUrl` と `movieId` を結合して作る
    #   （拡張子が必要な場合は下のコメントを参考にしてください）
    tags = []
    if row["tags"]:
        tags = [t for t in row["tags"].split(",") if t]

    created = None
    if row["createdAt"]:
        # 'YYYY-MM-DD HH:MM:SS' または ISO 形式を想定
        created = datetime.fromisoformat(row["createdAt"])

    # 動画ファイルに拡張子が必要な場合は、以下のように。
    # file_url_with_ext = f"{row['baseUrl'].rstrip('/')}/{row['movieId']}.mp4"

    # 生成日時は日本時間 (Asia/Tokyo) で返す
    tz_jp = ZoneInfo("Asia/Tokyo")
    if created:
        # created がナイーブ（tzinfo=None）であれば UTC と仮定して JST に変換
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc).astimezone(tz_jp)
        else:
            created = created.astimezone(tz_jp)

    return Video(
        title=row["title"],
        tags=tags,
        location=row["location"],
        generateDate=created or datetime.now(tz_jp),
        baseUrl=row["baseUrl"],
        movieId=row["movieId"],
        url=(f"{row['baseUrl'].rstrip('/')}/{row['movieId']}")
    )


def row_to_camera(row: sqlite3.Row) -> Camera:
    # DB の行 (Row) を Camera モデルへ変換するヘルパー
    return Camera(
        name=row["name"],
        id=row["id"],
        coordinate=Coordinate(lat=row["latitude"], lng=row["longitude"]),
        url=row["url"],
    )


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

    # DB から動画を取得する際に SQL を組み立ててフィルタリングする
    conn = get_conn()
    try:
        cur = conn.cursor()

        query = "SELECT * FROM videos WHERE 1=1"
        params: List[object] = []

        # q（タイトル or location の部分一致検索）
        if q:
            query += " AND (title LIKE ? OR location LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%"])

        # tags（AND 条件でフィルタ）。DB 側の tags はカンマ区切りの文字列なので
        # "," || tags || "," LIKE '%,tag,%' の形式で完全一致に近い検索を行う。
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            for t in tag_list:
                query += " AND (',' || tags || ',') LIKE ?"
                params.append(f"%,{t},%")

        query += " ORDER BY createdAt DESC"

        if limit:
            # limit は Query で型制約済みのため直接埋め込む
            query += f" LIMIT {limit}"

        cur.execute(query, params)
        rows = cur.fetchall()
        results: List[Video] = [row_to_video(r) for r in rows]
    finally:
        conn.close()

    return results

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

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT tags FROM videos ORDER BY createdAt ASC")
        seen = set()
        tags: List[str] = []
        for row in cur.fetchall():
            tstr = row["tags"]
            if not tstr:
                continue
            for t in [x.strip() for x in tstr.split(",") if x.strip()]:
                if t not in seen:
                    seen.add(t)
                    tags.append(t)
    finally:
        conn.close()

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

    conn = get_conn()
    try:
        cur = conn.cursor()

        # fetch matching videos
        # リクエストに videos が空の場合は早期リターンする（finally で接続は閉じられる）
        if not request.videos:
            return []

        placeholders = ",".join(["?"] * len(request.videos))
        cur.execute(f"SELECT * FROM videos WHERE movieId IN ({placeholders})", tuple(request.videos))
        rows = cur.fetchall()
        id_map = {row["movieId"]: row_to_video(row) for row in rows}

        results: List[Video] = []
        for vid in request.videos:
            video = id_map.get(vid)
            if video:
                results.append(video)

        return results
    finally:
        conn.close()

# カメラ情報取得API
@app.get("/cameras/{id}", response_model=Camera)
def get_camera(id: str):
    """
    カメラ情報取得API
    GET /cameras/{id}
    """

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM cameras WHERE id = ?", (id,))
        row = cur.fetchone()
        if row:
            return row_to_camera(row)
        raise HTTPException(status_code=404, detail="camera not found")
    finally:
        conn.close()
