from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import requests
from zoneinfo import ZoneInfo
import os
import uuid
try:
    import boto3
except ImportError:
    boto3 = None

from dotenv import load_dotenv
from fastapi import FastAPI, Query, status, HTTPException
# from fastapi import UploadFile, File
from pydantic import BaseModel
import logging

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# .envファイルから環境変数を読み込む
load_dotenv()

app = FastAPI(
    title="アゲアップAPI",
    description="動画検索・アゲ報告API",
    version="1.0.0"
)


import random

@app.on_event("startup")
def init_db():
    """
    アプリ起動時にSQLiteデータベースを初期化する。
    テーブルが存在しない場合は作成する。
    """
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        # videosテーブル作成
        cur.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                tags TEXT,
                location TEXT,
                baseUrl TEXT,
                movieId TEXT UNIQUE,
                createdAt TEXT
            )
        """)
        # camerasテーブル作成
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cameras (
                id TEXT PRIMARY KEY,
                name TEXT,
                latitude REAL,
                longitude REAL,
                url TEXT
            )
        """)
        conn.commit()
        print("✅ Database initialized successfully")
    except sqlite3.Error as e:
        print(f"❌ Database initialization error: {e}")
    finally:
        conn.close()

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
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    generateDate: Optional[datetime] = None

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
        url=(f"{row['baseUrl'].rstrip('/')}/{row['movieId']}.mp4")
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
    except Exception as e:
        # デバッグ用にエラー詳細を出力
        import traceback
        print(f"Error in list_videos: {e}")
        print(f"Query: {query}")
        print(f"Params: {params}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"動画検索でエラーが発生しました: {str(e)}")
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
    # ラズパイ上のカメラにアクセスして動画を取得し、R2へ保存してDBにメタデータを登録する。
    # location に ".raspi.local" を付与してラズパイのホストへアクセスする想定。
    
    logger.info(f"Received report request from user: {report.user}, location: {report.location}")

    # 1) ラズパイから動画を取得
    raspi_host = f"http://{report.location}.easy-hacking.com/videos?time=60"
    logger.info(f"Fetching video from camera: {raspi_host}")
    
    try:
        resp = requests.get(raspi_host, stream=True, timeout=600)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch video from {raspi_host}: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"カメラからの動画取得に失敗しました: {e}")

    if resp.status_code != 200:
        logger.error(f"Camera returned non-200 status code: {resp.status_code}")
        raise HTTPException(status_code=502, detail=f"カメラが正常なレスポンスを返しませんでした: {resp.status_code}")
    
    logger.info("Successfully fetched video from camera")

    # 2) R2へアップロード
    bucket = os.getenv("R2_BUCKET", "agaru-up-videos")
    movie_id = str(uuid.uuid4())  # movieId（拡張子なし）
    r2_key = f"{movie_id}.mp4"  # R2のファイル名（拡張子付き）
    logger.info(f"Uploading to R2 bucket: {bucket}, key: {r2_key}")

    try:
        s3 = _get_s3_client()
    except RuntimeError as e:
        logger.error("Failed to initialize R2 client", exc_info=True)
        raise HTTPException(status_code=500, detail=f"R2クライアントの初期化に失敗しました: {e}")

    try:
        # response.raw はファイルライクオブジェクトなので直接渡せる
        resp.raw.decode_content = True
        content_type = resp.headers.get("Content-Type", "video/mp4")
        s3.upload_fileobj(resp.raw, bucket, r2_key, ExtraArgs={"ContentType": content_type})
        logger.info("Successfully uploaded video to R2")
    except Exception as e:
        logger.error(f"Failed to upload to R2: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"R2へのアップロードに失敗しました: {e}")

    # アップロード成功 URL を構築
    # 公開URLを使用（.envのR2_PUBLIC_URLまたはデフォルト）
    public_url = os.getenv("R2_PUBLIC_URL", "https://pub-fe496443fb104153b0da8cceaccc6aea.r2.dev")
    file_url = f"{public_url.rstrip('/')}/{r2_key}"

    # 3) DBへ保存（videosテーブルのスキーマに従って保存）
    logger.info("Saving metadata to database...")
    conn = get_conn()
    try:
        cur = conn.cursor()
        # generateDate をリクエストから受け取るか現在時刻（日本時間）を使う
        tz_jp = ZoneInfo("Asia/Tokyo")
        if report.generateDate:
            gd = report.generateDate
            if gd.tzinfo is None:
                # naive は UTC とみなす
                gd = gd.replace(tzinfo=timezone.utc)
            created_at_dt = gd.astimezone(tz_jp)
        else:
            created_at_dt = datetime.now(tz_jp)

        # 格納は ISO 形式（秒精度）にする
        created_at = created_at_dt.replace(microsecond=0).isoformat()

        base_url = public_url  # 公開URLをbaseUrlとして保存

        # 未来創造展で上がった瞬間のタイトル候補リスト
        FUTURE_TITLES = [
            "未来創造展で最高の作品に出会った！",
            "これが未来だ！テンション爆上げ中！",
            "未来創造展で感動の瞬間をキャッチ！",
            "学生の創造力がヤバすぎる！アガる！",
            "未来創造展2026、熱気がスゴい！",
            "HAL大阪の技術力に圧倒された！",
            "未来を感じてテンションMAX！",
            "クリエイターの情熱に心が震えた！",
            "未来創造展で夢が広がる瞬間！",
            "最先端の技術に出会ってアガりまくり！",
            "こんな作品見たことない！感動！",
            "未来創造展、期待を超えてきた！",
        ]

        # title/tags はリクエストの値を優先、それ以外はデフォルト値
        # タイトルが未指定の場合はランダムに選択して、ユーザー名を頭につける
        title = report.title or random.choice(FUTURE_TITLES)
        tags_str = ""
        tags = ["未来創造展", "アガる", "未来創造展2026", "HAL大阪"]
        if tags:
            # リストをカンマ区切りで格納
            tags_str = ",".join([t.strip() for t in tags if t.strip()])

        # location に report.location（カメラID）を格納
        cur.execute(
            "INSERT INTO videos (title, tags, location, baseUrl, movieId, createdAt) VALUES (?, ?, ?, ?, ?, ?)",
            (title, tags_str, report.location, base_url, movie_id, created_at),
        )
        conn.commit()
        logger.info(f"Successfully saved to DB with movieId: {movie_id}")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}", exc_info=True)
        # DB保存に失敗した場合、アップロード済みオブジェクトを削除することも検討できますが
        # ここではエラーを返す。
        raise HTTPException(status_code=500, detail=f"データベースへの保存に失敗しました: {e}")
    finally:
        conn.close()

    return {"message": "アゲ報告を受け付けました", "user": report.user, "location": report.location, "movieId": movie_id, "url": file_url}

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
        # DISTINCTでユニークなtags文字列を取得
        cur.execute("SELECT DISTINCT tags FROM videos WHERE tags IS NOT NULL AND tags != '' ORDER BY createdAt ASC")
        seen: set[str] = set()
        unique_tags: List[str] = []
        for row in cur.fetchall():
            tstr = row["tags"]
            if not tstr:
                continue
            # カンマ区切りの各タグを分解して重複除去
            for t in [x.strip() for x in tstr.split(",") if x.strip()]:
                if t not in seen:
                    seen.add(t)
                    unique_tags.append(t)
    finally:
        conn.close()

    return unique_tags

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
        raise HTTPException(status_code=404, detail=f"Camera not found: {id}")
    finally:
        conn.close()


# ------------------------------------------------------------
# R2 クライアント取得ヘルパー
# 環境変数:
# - R2_ENDPOINT (例: https://<account-id>.r2.cloudflarestorage.com)
# - R2_ACCESS_KEY_ID
# - R2_SECRET_ACCESS_KEY
# - R2_BUCKET (デフォルト: agaru-up-videos)
# ------------------------------------------------------------


def _get_s3_client():
    if boto3 is None:
        raise RuntimeError("boto3 is required for R2 uploads. Install with `pip install boto3`.")

    endpoint = os.getenv("R2_ENDPOINT", "https://21b073b9670215c4e64a2c3e6525f259.r2.cloudflarestorage.com")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")

    # クォートが含まれている場合に除去する処理を追加
    if access_key:
        access_key = access_key.strip('"\'')
    if secret_key:
        secret_key = secret_key.strip('"\'')

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
