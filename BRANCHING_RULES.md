# ブランチ規則 (Branching Rules)

## 概要
このドキュメントは、AgaruUpプロジェクトにおけるGitFlowベースのブランチ管理規則を定義します。
小規模なチーム開発に適した、シンプルで効率的なワークフローを採用しています。

## ブランチの種類

### 1. メインブランチ (Main Branches)

#### `main`
- **目的**: 本番環境にデプロイ可能な安定したコード
- **特徴**: 常にリリース可能な状態を維持
- **マージ条件**:
  - リリースブランチからのマージのみ
  - プルリクエスト必須
  - レビュー承認必須

#### `dev`
- **目的**: 開発の中心となるブランチ
- **特徴**: 次のリリースに向けた機能統合
- **マージ条件**:
  - フィーチャーブランチからのマージ
  - プルリクエスト推奨

### 2. サポートブランチ (Supporting Branches)

#### フィーチャーブランチ (`feat/*`)
- **命名規則**: `feat/[機能名]` または `feat/[issue番号]-[機能名]`
- **例**:
  - `feat/user-authentication`
  - `feat/123-profile-screen`
- **作成元**: `dev`
- **マージ先**: `dev`
- **ライフサイクル**: 機能開発完了まで
- **削除**: マージ後に削除

#### リリースブランチ (`release/*`)
- **命名規則**: `release/[バージョン]`
- **例**: `release/1.0.0`, `release/1.1.0`
- **作成元**: `dev`
- **マージ先**: `main` および `dev`
- **目的**: リリース準備（バグフィックス、バージョン更新）
- **削除**: リリース完了後に削除

#### ホットフィックスブランチ (`hotfix/*`)
- **命名規則**: `hotfix/[バージョン]` または `hotfix/[問題の説明]`
- **例**: `hotfix/1.0.1`, `hotfix/critical-crash-fix`
- **作成元**: `main`
- **マージ先**: `main` および `dev`
- **目的**: 緊急の本番バグ修正
- **削除**: 修正完了後に削除

## ワークフロー

### 1. 新機能開発
```bash
# devブランチから新機能ブランチを作成
git checkout dev
git pull origin dev
git checkout -b feat/new-feature

# 開発作業...
git add .
git commit -m "feat: 新機能の実装"

# devにマージ
git checkout dev
git pull origin dev
git merge --no-ff feat/new-feature
git push origin dev
git branch -d feat/new-feature
```

### 2. リリース準備
```bash
# devからリリースブランチを作成
git checkout dev
git pull origin dev
git checkout -b release/1.0.0

# リリース準備作業（バージョン更新、バグフィックス）
git add .
git commit -m "chore: バージョン1.0.0のリリース準備"

# mainにマージ
git checkout main
git merge --no-ff release/1.0.0
git tag -a v1.0.0 -m "Version 1.0.0"

# devにもマージ
git checkout dev
git merge --no-ff release/1.0.0

# プッシュ
git push origin main
git push origin dev
git push origin --tags

# リリースブランチ削除
git branch -d release/1.0.0
```

### 3. ホットフィックス
```bash
# mainからホットフィックスブランチを作成
git checkout main
git pull origin main
git checkout -b hotfix/1.0.1

# 修正作業...
git add .
git commit -m "fix: 緊急バグ修正"

# mainにマージ
git checkout main
git merge --no-ff hotfix/1.0.1
git tag -a v1.0.1 -m "Version 1.0.1"

# devにもマージ
git checkout dev
git merge --no-ff hotfix/1.0.1

# プッシュ
git push origin main
git push origin dev
git push origin --tags

# ホットフィックスブランチ削除
git branch -d hotfix/1.0.1
```

## コミットメッセージ規則

### 形式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### タイプ (Type)
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `style`: コードスタイルの変更
- `refactor`: リファクタリング
- `test`: テストの追加・修正
- `chore`: その他の変更

### 例
```
feat(auth): ユーザー認証機能を追加

- ログイン画面の実装
- Firebase Authenticationとの連携
- バイオメトリクス認証のサポート

Closes #123
```

## プルリクエスト規則

### 必須条件
- [ ] 適切なブランチから作成されている
- [ ] コンフリクトが解決されている
- [ ] テストが通っている
- [ ] コードレビューを受けている

### テンプレート
```markdown
## 概要
このプルリクエストの概要を記述

## 変更内容
- 変更点1
- 変更点2

## テスト
- [ ] 既存のテストが通る
- [ ] 新規テストを追加済み
- [ ] 手動テストを実施済み

## チェックリスト
- [ ] コードスタイルガイドに従っている
- [ ] 適切なコメントを追加している
- [ ] ドキュメントを更新している（必要な場合）

## 関連Issue
Closes #[issue番号]
```

## タグ付けルール

### バージョニング
Semantic Versioning (SemVer) を採用

- **MAJOR**: 破壊的変更
- **MINOR**: 後方互換性のある新機能
- **PATCH**: 後方互換性のあるバグ修正

### 例
- `v1.0.0`: 初回リリース
- `v1.1.0`: 新機能追加
- `v1.1.1`: バグ修正

## ブランチ保護設定

### `main`ブランチ
- 直接プッシュ禁止
- プルリクエスト必須
- レビュー承認必須
- ステータスチェック必須

### `dev`ブランチ
- 直接プッシュ許可（小規模チームの場合）
- プルリクエスト推奨

## よくある質問

### Q: 小さな修正でもブランチを作成する必要がありますか？
A: はい。どんな小さな変更でも、トレーサビリティとレビューのためにブランチを作成することを推奨します。

### Q: リリースブランチでの作業内容は？
A: バージョン番号の更新、ドキュメントの更新、軽微なバグフィックスのみ。新機能の追加は禁止。

### Q: ホットフィックスとバグフィックスの違いは？
A: ホットフィックスは本番環境の緊急修正、バグフィックスは通常の開発サイクル内での修正です。

---

**最終更新**: 2025年11月28日
