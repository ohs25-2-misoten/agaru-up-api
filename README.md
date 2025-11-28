# AgaruUpAPI

AgaruUpAPIは、iOSアプリとバックエンド間を繋ぐAPIサーバーです。
動画検索、アゲ報告、タグリスト取得、動画UUID指定検索などの機能を提供します。

## 📱 概要

AgaruUpは、ユーザーが日常生活の中で遭遇した『アガる』出来事をニュース化して共有できるプラットフォームです。
このAPIは、iOSアプリからの動画情報の取得やアゲ報告を受け付けるバックエンドサービスを提供します。

## 🛠️ 技術スタック

- **言語**: Python 3.8+
- **フレームワーク**: FastAPI

## 🚀 セットアップ

### 必要条件

- Python 3.8 以降

### インストール手順

1. リポジトリをクローンします：
```bash
git clone https://github.com/ohs25-2-misoten/agaru-up-api.git
cd agaru-up-api
```

## 📁 プロジェクト構造

```
agaru-up-api/
└── agaru_up_api.py          # FastAPIアプリケーション本体
```

## 🔄 開発ワークフロー

このプロジェクトでは、GitFlowベースのブランチ戦略を採用しています。

### ブランチ規則

- `main`: 本番環境用の安定したコード
- `dev`: 開発の中心となるブランチ
- `feat/*`: 新機能開発用ブランチ
- `release/*`: リリース準備用ブランチ
- `hotfix/*`: 緊急修正用ブランチ

詳細は [BRANCHING_RULES.md](./BRANCHING_RULES.md) を参照してください。

### 新機能開発の流れ

1. devブランチから機能ブランチを作成：
```bash
git checkout dev
git pull origin dev
git checkout -b feat/your-feature-name
```

2. 開発・コミット：
```bash
git add .
git commit -m "feat: 新機能の説明"
```

3. プルリクエストを作成してdevにマージ

## 📝 コーディング規約

### コミットメッセージ

Conventional Commits形式を採用：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**タイプ**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: スタイル変更
- `refactor`: リファクタリング
- `test`: テスト
- `chore`: その他

### Pythonコーディングスタイル

- PEP 8スタイルガイドに準拠

## 🚢 リリース

### バージョニング

Semantic Versioning (SemVer) を採用：
- `MAJOR.MINOR.PATCH` (例: 1.0.0)

### リリースプロセス

1. devからreleaseブランチを作成
2. バージョン更新とリリース準備
3. mainにマージしてタグ付け

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feat/amazing-feature`)
3. 変更をコミット (`git commit -m 'feat: 素晴らしい機能を追加'`)
4. ブランチにプッシュ (`git push origin feat/amazing-feature`)
5. プルリクエストを作成

### プルリクエストガイドライン

- [ ] 適切なブランチから作成
- [ ] テストの追加・更新
- [ ] コードレビューの実施
- [ ] コンフリクトの解決
- [ ] ドキュメントの更新（必要な場合）

## 📄 ライセンス

GNU Affero General Public License v3.0 (AGPL-3.0) ライセンスの下で提供されています。詳細は [LICENSE](./LICENSE) ファイルを参照してください。

## 👥 メンテナー

- [tomo3101](mailto:tacstomo.sub@gmail.com)

## 📞 サポート

質問や問題がある場合は、以下の方法でお問い合わせください：

- [Issues](../../issues) - バグ報告や機能要望
- [Discussions](../../discussions) - 質問や議論

## 📚 追加リソース

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python Official Documentation](https://docs.python.org/3/)

---

**最終更新**: 2025年11月28日
