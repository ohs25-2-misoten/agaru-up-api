# Agaru Up API

動画検索・アゲ報告API for 未来創造展2026

## 必要要件

- Cloudflare アカウント（R2バケットと Cloudflare Tunnel のセットアップが必須）
- [mise](https://mise.jdx.dev/) - 開発環境管理ツール
- [1Password CLI](https://developer.1password.com/docs/cli/) - シークレット管理
- [Docker](https://www.docker.com/) - コンテナ実行環境
- [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) - Cloudflare Tunnel

### Cloudflare の事前セットアップ

- R2 を使う場合: Cloudflare で R2 バケットを作成し、Access Key/Secret を発行しておきます。
- アプリを外部公開する場合: Cloudflare Tunnel を作成し、トークンを取得して `.env` の `CLOUDFLARE_TUNNEL_TOKEN` に設定します。
- R2 ではなく AWS S3 などの S3 互換ストレージも利用可能です。S3 のバケットと IAM ユーザーを用意し、後述の `R2_*` 環境変数に S3 の値を入れてください（名前はそのままで動作します）。

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd agaru-up-api
```

### 2. mise のインストールと環境構築

```bash
# mise をインストール（未インストールの場合）
curl https://mise.run | sh

# Python 3.14.2 をインストール
mise install
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

#### 方法A: 1Password CLI を使用する場合（推奨）

`.env` ファイルは1Password参照形式で設定されています。

```bash
# 1Password にサインイン
op signin
```

#### 方法B: 1Passwordを使用しない場合

`.env.local` ファイルを作成し、実際の値を直接設定します：

```bash
cp .env .env.local
```

`.env.local` を編集して、1Password参照を実際の値に置き換えます：

```env
R2_ENDPOINT=https://21b073b9670215c4e64a2c3e6525f259.r2.cloudflarestorage.com
R2_BUCKET=agaru-up-videos
R2_ACCESS_KEY_ID=your_actual_access_key_id
R2_SECRET_ACCESS_KEY=your_actual_secret_access_key
R2_PUBLIC_URL=https://pub-fe496443fb104153b0da8cceaccc6aea.r2.dev
CLOUDFLARE_TUNNEL_TOKEN=your_actual_tunnel_token
```

S3 を使う場合の例（`R2_*` 名のまま S3 の値を設定します）:

```env
R2_ENDPOINT=https://s3.ap-northeast-1.amazonaws.com
R2_BUCKET=your_s3_bucket
R2_ACCESS_KEY_ID=your_aws_access_key_id
R2_SECRET_ACCESS_KEY=your_aws_secret_access_key
R2_PUBLIC_URL=https://your_s3_bucket.s3.ap-northeast-1.amazonaws.com
CLOUDFLARE_TUNNEL_TOKEN=your_actual_tunnel_token
```

> ⚠️ **注意**: `.env.local` には機密情報が含まれるため、Gitにコミットしないでください。

## 開発用コマンド

mise を使用してタスクを実行できます：

```bash
# ローカルで API を起動（ホットリロード有効）
mise run dev

# 1Password CLI を使用して API を起動
mise run dev:op
```

## Docker を使用した実行

```bash
# Docker イメージをビルド
mise run docker:build

# コンテナを起動（1Password からシークレットを注入）
mise run docker:run

# コンテナを停止・削除
mise run docker:down
```

## 公開用（Cloudflare Tunnel）

```bash
# Docker コンテナ + Cloudflare Tunnel で公開
mise run docker:run:public
```

## API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/videos` | 動画一覧取得（検索可能） |
| POST | `/videos/bulk` | 複数UUIDで動画を一括取得 |
| POST | `/report` | アゲ報告（動画アップロード） |
| GET | `/tags` | タグ一覧取得 |
| GET | `/cameras/{id}` | カメラ情報取得 |

### 動画検索パラメータ

| パラメータ | 説明 |
|-----------|------|
| `q` | 検索ワード（タイトル・ロケーション） |
| `tags` | タグ（カンマ区切り） |
| `limit` | 取得件数（1-50、デフォルト: 10） |

## プロジェクト構成

```
agaru-up-api/
├── app/
│   └── agaru_up_api.py  # メインAPIアプリケーション
├── Dockerfile           # Docker設定
├── mise.toml            # mise タスク定義
├── requirements.txt     # Python依存関係
├── .env                 # 環境変数（1Password参照形式）
└── README.md            # このファイル
```

## ライセンス

See [LICENSE](LICENSE) file.
