import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import urllib.parse
from datetime import datetime

# ページ設定
st.set_page_config(page_title="シフト読み取りアプリ", page_icon="📅")
st.title("📅 シフト読み取りアプリ")

# --- 🔑 APIキー設定 ---
try:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ エラー: APIキーが見つかりません。")
        st.stop()

    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    st.caption(f"System Status: Online (AI Tool Version: {genai.__version__})")

except Exception as e:
    st.error(f"❌ 設定エラー: {e}")
    st.stop()

# --- 📱 アプリ本編 ---
my_name = st.text_input("あなたの名前（シフト表と同じ表記で）", "飯田")
hourly_wage = st.number_input("時給", value=1100)
year_month = st.text_input("年月（例：2026-01）", "2026-01")

uploaded_file = st.file_uploader("シフト表をアップロード", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='アップロード画像', use_container_width=True)
    
    if st.button("🚀 解析スタート"):
        with st.spinner("最新AI (gemini-2.5-flash) が解析中..."):
            try:
                # モデル指定
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""
                この画像はシフト表です。以下のデータをJSON形式で抽出してください。
                ターゲット名: {my_name}
                
                【超重要ルール】
                1. 日付は"{year_month}-01"形式
                2. 開始時間は"start"、終了時間は"end"というキー名にする。
                3. 時間は"09:30"形式 (9.5→09:30)。
                4. JSONリストのみ出力（```json不要）。
                
                例:
                [
                  {{"date": "2026-01-01", "start": "09:00", "end": "18:00"}},
                  {{"date": "2026-01-02", "start": "12:00", "end": "21:00"}}
                ]
                """
                
                response = model.generate_content([prompt, image])
                text = response.text.replace("```json", "").replace("```", "").strip()
                if text.startswith("json"): text = text[4:]
                
                # データ変換
                data = json.loads(text)
                
                st.balloons()
                st.success(f"🎉 {len(data)}件のシフトが見つかりました！")
                
                # --- 🛠 デバッグ用：AIが読み取った中身を見る ---
                with st.expander("🔍 AIが読み取った生データを確認する"):
                    st.write(data)
                # ---------------------------------------------

                total_salary = 0
                
                # データを1行ずつ処理
                for item in data:
                    try:
                        # データの安全確認（ここが追加ポイント！）
                        if "start" not in item or "end" not in item:
                            st.warning(f"⚠️ 読み取れない行がありました（スキップします）: {item}")
                            continue

                        start_str = f"{item['date']} {item['start']}"
                        end_str = f"{item['date']} {item['end']}"
                        
                        start = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
                        end = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
                        
                        # 給与計算
                        hours = (end - start).seconds / 3600
                        salary = hours * hourly_wage
                        total_salary += salary
                        
                        # リンク作成
                        title = urllib.parse.quote(f"バイト({item['start']}-{item['end']})")
                        dates = start.strftime("%Y%m%dT%H%M00") + "/" + end.strftime("%Y%m%dT%H%M00")
                        details = urllib.parse.quote(f"予想給与: ¥{int(salary):,}")
                        url = f"[https://www.google.com/calendar/render?action=TEMPLATE&text=](https://www.google.com/calendar/render?action=TEMPLATE&text=){title}&dates={dates}&details={details}"
                        
                        # 画面に表示
                        st.markdown(f"📅 **{item['date']}** ({item['start']}-{item['end']}) → [カレンダー追加]({url})")
                    
                    except Exception as e:
                        st.error(f"データ変換エラー: {e}")

                st.info(f"💰 予想給与合計: ¥{int(total_salary):,}")
                
            except Exception as e:
                st.error("解析エラーが発生しました。")
                st.write(f"エラー詳細: {e}")
