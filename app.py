import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="シフト読み取りアプリ", page_icon="📅")
st.title("📅 シフト読み取りアプリ（診断モード）")

# --- 🔑 APIキーの診断と接続 ---
try:
    # 1. Secrets自体が読めるかチェック
    if not st.secrets:
        st.error("❌ エラー: 「Secrets（金庫）」が空っぽです！")
        st.info("対処法: Manage app → Settings → Secrets にキーを保存してください。")
        st.stop()

    # 2. キーの名前が合っているかチェック
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ エラー: 'GEMINI_API_KEY' という名前のキーが見つかりません。")
        st.write("👇 現在保存されているキーの名前一覧:")
        st.write(list(st.secrets.keys()))
        st.info("対処法: Secretsの書き方が `GEMINI_API_KEY = \"AIza...\"` になっているか確認してください。")
        st.stop()

    # 3. 接続テスト
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    
    st.success("✅ APIキーの読み込みに成功しました！")

except Exception as e:
    st.error(f"❌ 予期せぬエラーが発生しました: {e}")
    st.stop()

# --- 📱 ここからアプリ本編 ---

# ユーザー設定
with st.expander("⚙️ 設定（名前・時給）", expanded=True):
    my_name = st.text_input("あなたの名前（シフト表と同じ漢字で）", "飯田")
    hourly_wage = st.number_input("時給", value=1100)
    year_month = st.text_input("年月（例：2026-01）", "2026-01")

# 画像アップロード
uploaded_file = st.file_uploader("シフト表の画像をアップロード", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='アップロード画像', use_container_width=True)
    
    if st.button("🚀 解析スタート"):
        with st.spinner("AIが解析中...（gemini-pro-vision使用）"):
            try:
                # 安定版モデルを指定
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                この画像はシフト表です。以下のデータをJSON形式で抽出してください。
                ターゲット名: {my_name}
                
                【抽出ルール】
                1. 日付は"{year_month}-01"形式
                2. 時間は"09:30"形式 (9.5→09:30, 20.0→20:00)
                3. 公休は無視
                4. 出力は純粋なJSONリスト形式のみ（```json は不要）
                """
                
                response = model.generate_content([prompt, image])
                text = response.text.replace("```json", "").replace("```", "").strip()
                if text.startswith("json"): text = text[4:] # ゴミとり
                
                data = json.loads(text)
                st.balloons()
                st.success(f"🎉 {len(data)}件のシフトが見つかりました！")
                
                total_salary = 0
                for item in data:
                    start = datetime.strptime(f"{item['date']} {item['start']}", "%Y-%m-%d %H:%M")
                    end = datetime.strptime(f"{item['date']} {item['end']}", "%Y-%m-%d %H:%M")
                    hours = (end - start).seconds / 3600
                    salary = hours * hourly_wage
                    total_salary += salary
                    
                    # リンク作成
                    title = urllib.parse.quote(f"バイト({item['start']}-{item['end']})")
                    dates = start.strftime("%Y%m%dT%H%M00") + "/" + end.strftime("%Y%m%dT%H%M00")
                    details = urllib.parse.quote(f"予想給与: ¥{int(salary):,}")
                    url = f"[https://www.google.com/calendar/render?action=TEMPLATE&text=](https://www.google.com/calendar/render?action=TEMPLATE&text=){title}&dates={dates}&details={details}"
                    
                    st.markdown(f"📅 **{item['date']}** ({item['start']}-{item['end']}) → [Googleカレンダー追加]({url})")
                
                st.info(f"💰 予想給与合計: ¥{int(total_salary):,}")
                
            except Exception as e:
                st.error(f"解析エラー: {e}")
                st.write("ヒント: 画像にあなたの名前が写っていないか、AIが読み取れませんでした。")
