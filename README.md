# ffxiv-rss-actions

Discord などの WebHook と Lodestone の RSS をいい感じにつなげる Actions です。

日本語のニュースにのみ対応しています。需要がありそうなら多言語対応します。

## 環境変数の設定方法

1. 「Settings」タブをクリックします。
2. 左側のメニューから「Secrets and variables」 > 「Actions」を選択します。
3. 「New repository secret」ボタンをクリックします。
4. 名前に WEBHOOK_URL と入力し、値に Webhook URL を入力して「Add secret」ボタンをクリックします。

## PvP ステージスケジュール投稿

同じ Discord Webhook メッセージに、投稿時のステージから7枠分の開始時刻と、毎週繰り返す週間時刻表を表示します。各ステージは開始から60分間です。

開始時刻は Discord の閲覧者の現地時刻で表示されます。たとえば「17:00 クラウドナイン」「18:00 東方絡繰御殿」とあれば、18:00 からは東方絡繰御殿です。一覧の最後の枠が終わった後は、週間時刻表を使ってください。日本時間で直近の開始時刻の行と、その曜日の列を引き、そこにある番号をステージ名の横の番号と照合します。

追加で以下を設定してください。

- Secret: `DISCORD_STAGE_WEBHOOK_URL`
- Variable: `STAGE_ZERO_TIME`（省略可。既定値は `2026-05-03T00:00:00+09:00`）

`STAGE_ZERO_TIME` には「パライストラ」が始まる基準時刻を ISO 形式で指定します。例:

```text
2026-05-03T00:00:00+09:00
```

GitHub Actions は RSS 更新と同じタイミングで起動し、ローテーションまたは投稿形式が変わるとメッセージを編集します。実行が遅れても、ローテーションのルールと基準時刻が同じ間は週間時刻表を使えます。作成された Discord メッセージ ID は `stage_schedule_state.json` に保存されます。
