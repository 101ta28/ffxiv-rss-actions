# ffxiv-rss-actions

Discord などの WebHook と Lodestone の RSS をいい感じにつなげる Actions です。

日本語のニュースにのみ対応しています。需要がありそうなら多言語対応します。

## 環境変数の設定方法

1. 「Settings」タブをクリックします。
2. 左側のメニューから「Secrets and variables」 > 「Actions」を選択します。
3. 「New repository secret」ボタンをクリックします。
4. 名前に WEBHOOK_URL と入力し、値に Webhook URL を入力して「Add secret」ボタンをクリックします。

## PvP ステージスケジュール投稿

同じ Discord Webhook メッセージを更新し続ける方式で、現在のステージと次回ステージを投稿できます。

追加で以下を設定してください。

- Secret: `DISCORD_STAGE_WEBHOOK_URL`
- Variable: `STAGE_ZERO_TIME`（省略可。既定値は `2026-05-03T00:00:00+09:00`）

`STAGE_ZERO_TIME` には「パライストラ」が始まる基準時刻を ISO 形式で指定します。例:

```text
2026-05-03T00:00:00+09:00
```

GitHub Actions は既存の RSS 更新と同じタイミングで実行されますが、ステージ投稿はローテーションが変わったときだけ編集します。作成された Discord メッセージ ID は `stage_schedule_state.json` に保存されます。
